#include "motion_estimation.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cctype>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>

namespace me {
namespace {

std::string next_pgm_token(std::istream& input) {
    std::string token;
    char ch = '\0';
    while (input.get(ch)) {
        if (ch == '#') {
            input.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            continue;
        }
        if (!std::isspace(static_cast<unsigned char>(ch))) {
            token.push_back(ch);
            break;
        }
    }
    while (input.get(ch)) {
        if (std::isspace(static_cast<unsigned char>(ch))) {
            break;
        }
        if (ch == '#') {
            input.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            break;
        }
        token.push_back(ch);
    }
    if (token.empty()) {
        throw std::runtime_error("Unexpected end of PGM header");
    }
    return token;
}

int parse_integer(const std::string& token, const char* field, bool allow_zero = false) {
    std::size_t consumed = 0;
    int result = 0;
    try {
        result = std::stoi(token, &consumed);
    } catch (const std::exception&) {
        throw std::runtime_error(std::string("Invalid PGM ") + field + ": " + token);
    }
    if (consumed != token.size() || result < 0 || (!allow_zero && result == 0)) {
        throw std::runtime_error(std::string("Invalid PGM ") + field + ": " + token);
    }
    return result;
}

void validate_pair(const Image& reference, const Image& current) {
    if (reference.width <= 0 || reference.height <= 0 || current.width <= 0 || current.height <= 0) {
        throw std::invalid_argument("Image dimensions must be positive");
    }
    if (reference.width != current.width || reference.height != current.height) {
        throw std::invalid_argument("Reference and current images must have identical dimensions");
    }
    const auto expected = static_cast<std::size_t>(reference.width) * static_cast<std::size_t>(reference.height);
    if (reference.pixels.size() != expected || current.pixels.size() != expected) {
        throw std::invalid_argument("Image pixel buffers do not match their dimensions");
    }
}

struct SearchContext {
    const Image& reference;
    const Image& current;
    int x;
    int y;
    int width;
    int height;
    int search_range;
    std::unordered_set<std::uint64_t> visited;
    MotionVector best{};
    std::uint64_t best_sad{std::numeric_limits<std::uint64_t>::max()};
    std::uint64_t candidates{};

    SearchContext(const Image& ref, const Image& cur, int bx, int by, int bw, int bh, int range)
        : reference(ref), current(cur), x(bx), y(by), width(bw), height(bh), search_range(range) {
        visited.reserve(static_cast<std::size_t>((2 * range + 1) * (2 * range + 1)));
    }

    bool valid(int dx, int dy) const {
        if (dx < -search_range || dx > search_range || dy < -search_range || dy > search_range) {
            return false;
        }
        const int rx = x + dx;
        const int ry = y + dy;
        return rx >= 0 && ry >= 0 && rx + width <= reference.width && ry + height <= reference.height;
    }

    std::uint64_t evaluate(int dx, int dy) {
        if (!valid(dx, dy)) {
            return std::numeric_limits<std::uint64_t>::max();
        }
        const auto key = (static_cast<std::uint64_t>(static_cast<std::uint32_t>(dy + search_range))
                          << 32U) |
                         static_cast<std::uint32_t>(dx + search_range);
        if (!visited.insert(key).second) {
            return sad_at(dx, dy);
        }
        ++candidates;
        const std::uint64_t value = sad_at(dx, dy);
        // Stable tie-breaking: retain the earlier winner when SAD is equal.
        if (value < best_sad) {
            best_sad = value;
            best = {dx, dy};
        }
        return value;
    }

    std::uint64_t sad_at(int dx, int dy) const {
        std::uint64_t sum = 0;
        const int rx = x + dx;
        const int ry = y + dy;
        for (int row = 0; row < height; ++row) {
            for (int col = 0; col < width; ++col) {
                const int a = static_cast<int>(current.at(x + col, y + row));
                const int b = static_cast<int>(reference.at(rx + col, ry + row));
                sum += static_cast<std::uint64_t>(std::abs(a - b));
            }
        }
        return sum;
    }
};

std::vector<MotionVector> large_diamond() {
    return {{0, 0}, {0, -2}, {-1, -1}, {1, -1}, {-2, 0}, {2, 0}, {-1, 1}, {1, 1}, {0, 2}};
}

std::vector<MotionVector> small_diamond() {
    return {{0, 0}, {0, -1}, {-1, 0}, {1, 0}, {0, 1}};
}

void search_full(SearchContext& context) {
    for (int dy = -context.search_range; dy <= context.search_range; ++dy) {
        for (int dx = -context.search_range; dx <= context.search_range; ++dx) {
            context.evaluate(dx, dy);
        }
    }
}

void search_three_step(SearchContext& context) {
    context.evaluate(0, 0);
    int step = 1;
    while (step <= context.search_range / 2) {
        step *= 2;
    }
    if (context.search_range > 0 && step < context.search_range) {
        // The power-of-two schedule remains inside the configured search window.
    }
    while (step >= 1) {
        const MotionVector center = context.best;
        for (int dy : {-step, 0, step}) {
            for (int dx : {-step, 0, step}) {
                if (dx == 0 && dy == 0) {
                    continue;
                }
                context.evaluate(center.dx + dx, center.dy + dy);
            }
        }
        step /= 2;
    }
}

void search_diamond(SearchContext& context, MotionVector initial) {
    initial.dx = std::clamp(initial.dx, -context.search_range, context.search_range);
    initial.dy = std::clamp(initial.dy, -context.search_range, context.search_range);
    context.evaluate(initial.dx, initial.dy);
    if (context.best_sad == std::numeric_limits<std::uint64_t>::max()) {
        context.evaluate(0, 0);
    }

    const auto large = large_diamond();
    const auto small = small_diamond();
    const int max_iterations = (2 * context.search_range + 1) * (2 * context.search_range + 1) + 2;
    int iteration = 0;
    while (iteration++ < max_iterations) {
        const MotionVector center = context.best;
        for (const auto& offset : large) {
            context.evaluate(center.dx + offset.dx, center.dy + offset.dy);
        }
        const MotionVector after_large = context.best;
        if (after_large.dx != center.dx || after_large.dy != center.dy) {
            continue;
        }
        for (const auto& offset : small) {
            context.evaluate(center.dx + offset.dx, center.dy + offset.dy);
        }
        const MotionVector after_small = context.best;
        if (after_small.dx == center.dx && after_small.dy == center.dy) {
            break;
        }
    }
}

int median3(int a, int b, int c) {
    if (a > b) std::swap(a, b);
    if (b > c) std::swap(b, c);
    if (a > b) std::swap(a, b);
    return b;
}

}  // namespace

std::uint8_t Image::at(int x, int y) const {
    if (x < 0 || y < 0 || x >= width || y >= height) {
        throw std::out_of_range("Image coordinates out of range");
    }
    return pixels[static_cast<std::size_t>(y) * static_cast<std::size_t>(width) + static_cast<std::size_t>(x)];
}

std::uint8_t& Image::at(int x, int y) {
    if (x < 0 || y < 0 || x >= width || y >= height) {
        throw std::out_of_range("Image coordinates out of range");
    }
    return pixels[static_cast<std::size_t>(y) * static_cast<std::size_t>(width) + static_cast<std::size_t>(x)];
}

Image load_pgm(const std::string& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        throw std::runtime_error("Cannot open PGM file: " + path);
    }
    const std::string magic = next_pgm_token(input);
    if (magic != "P5" && magic != "P2") {
        throw std::runtime_error("Only 8-bit grayscale PGM (P5/P2) is supported: " + path);
    }
    Image image;
    image.width = parse_integer(next_pgm_token(input), "width");
    image.height = parse_integer(next_pgm_token(input), "height");
    const int max_value = parse_integer(next_pgm_token(input), "max value");
    if (max_value > 255) {
        throw std::runtime_error("Only 8-bit PGM images (max value <= 255) are supported");
    }
    const auto count = static_cast<std::size_t>(image.width) * static_cast<std::size_t>(image.height);
    image.pixels.resize(count);
    if (magic == "P5") {
        input.read(reinterpret_cast<char*>(image.pixels.data()), static_cast<std::streamsize>(count));
        if (input.gcount() != static_cast<std::streamsize>(count)) {
            throw std::runtime_error("PGM pixel data is truncated: " + path);
        }
        if (max_value != 255) {
            for (auto& pixel : image.pixels) {
                pixel = static_cast<std::uint8_t>((static_cast<int>(pixel) * 255) / max_value);
            }
        }
    } else {
        for (auto& pixel : image.pixels) {
            const int value = parse_integer(next_pgm_token(input), "pixel", true);
            if (value > max_value) {
                throw std::runtime_error("PGM pixel exceeds max value");
            }
            pixel = static_cast<std::uint8_t>((value * 255) / max_value);
        }
    }
    return image;
}

void save_pgm(const Image& image, const std::string& path) {
    if (image.width <= 0 || image.height <= 0 ||
        image.pixels.size() != static_cast<std::size_t>(image.width) * static_cast<std::size_t>(image.height)) {
        throw std::invalid_argument("Invalid image passed to save_pgm");
    }
    std::ofstream output(path, std::ios::binary);
    if (!output) {
        throw std::runtime_error("Cannot write PGM file: " + path);
    }
    output << "P5\n" << image.width << ' ' << image.height << "\n255\n";
    output.write(reinterpret_cast<const char*>(image.pixels.data()), static_cast<std::streamsize>(image.pixels.size()));
    if (!output) {
        throw std::runtime_error("Failed while writing PGM file: " + path);
    }
}

std::string algorithm_name(SearchAlgorithm algorithm) {
    switch (algorithm) {
        case SearchAlgorithm::FullSearch: return "full_search";
        case SearchAlgorithm::ThreeStep: return "three_step";
        case SearchAlgorithm::Diamond: return "diamond";
        case SearchAlgorithm::PredictiveDiamond: return "predictive_diamond";
    }
    throw std::invalid_argument("Unknown algorithm enum");
}

SearchAlgorithm parse_algorithm(const std::string& name) {
    if (name == "full_search") return SearchAlgorithm::FullSearch;
    if (name == "three_step") return SearchAlgorithm::ThreeStep;
    if (name == "diamond") return SearchAlgorithm::Diamond;
    if (name == "predictive_diamond") return SearchAlgorithm::PredictiveDiamond;
    throw std::invalid_argument("Unknown algorithm: " + name);
}

std::vector<BlockMotion> estimate_motion(const Image& reference, const Image& current, int block_size,
                                         int search_range, SearchAlgorithm algorithm) {
    validate_pair(reference, current);
    if (block_size <= 0) throw std::invalid_argument("block_size must be positive");
    if (search_range < 0 || search_range > 128) throw std::invalid_argument("search_range must be between 0 and 128");

    const int blocks_x = (current.width + block_size - 1) / block_size;
    const int blocks_y = (current.height + block_size - 1) / block_size;
    std::vector<BlockMotion> blocks;
    blocks.reserve(static_cast<std::size_t>(blocks_x) * static_cast<std::size_t>(blocks_y));
    std::vector<MotionVector> grid(static_cast<std::size_t>(blocks_x) * static_cast<std::size_t>(blocks_y));

    for (int by = 0; by < current.height; by += block_size) {
        for (int bx = 0; bx < current.width; bx += block_size) {
            const int bw = std::min(block_size, current.width - bx);
            const int bh = std::min(block_size, current.height - by);
            SearchContext context(reference, current, bx, by, bw, bh, search_range);
            if (algorithm == SearchAlgorithm::FullSearch) {
                search_full(context);
            } else if (algorithm == SearchAlgorithm::ThreeStep) {
                search_three_step(context);
            } else {
                MotionVector predictor{};
                if (algorithm == SearchAlgorithm::PredictiveDiamond) {
                    const int ix = bx / block_size;
                    const int iy = by / block_size;
                    const auto get = [&](int gx, int gy) -> MotionVector {
                        if (gx < 0 || gy < 0 || gx >= blocks_x || gy >= blocks_y) return {};
                        return grid[static_cast<std::size_t>(gy) * static_cast<std::size_t>(blocks_x) + static_cast<std::size_t>(gx)];
                    };
                    const MotionVector left = get(ix - 1, iy);
                    const MotionVector top = get(ix, iy - 1);
                    const MotionVector top_right = get(ix + 1, iy - 1);
                    predictor.dx = std::clamp(median3(left.dx, top.dx, top_right.dx), -search_range, search_range);
                    predictor.dy = std::clamp(median3(left.dy, top.dy, top_right.dy), -search_range, search_range);
                }
                search_diamond(context, predictor);
            }
            if (context.best_sad == std::numeric_limits<std::uint64_t>::max()) {
                // This can occur only for a degenerate boundary/search setup; keep the result deterministic.
                context.evaluate(0, 0);
            }
            BlockMotion result;
            result.block_x = bx;
            result.block_y = by;
            result.block_width = bw;
            result.block_height = bh;
            result.vector = context.best;
            result.sad = context.best_sad;
            result.candidates_evaluated = context.candidates;
            const auto grid_index = static_cast<std::size_t>(by / block_size) * static_cast<std::size_t>(blocks_x) + static_cast<std::size_t>(bx / block_size);
            grid[grid_index] = result.vector;
            blocks.push_back(result);
        }
    }
    return blocks;
}

BenchmarkMetrics benchmark(const Image& reference, const Image& current, int block_size, int search_range,
                           SearchAlgorithm algorithm) {
    validate_pair(reference, current);
    const auto start = std::chrono::steady_clock::now();
    const auto blocks = estimate_motion(reference, current, block_size, search_range, algorithm);
    const auto stop = std::chrono::steady_clock::now();
    const double elapsed_ms = std::chrono::duration<double, std::milli>(stop - start).count();

    std::uint64_t total_sad = 0;
    std::uint64_t total_candidates = 0;
    std::uint64_t squared_error = 0;
    for (const auto& block : blocks) {
        total_sad += block.sad;
        total_candidates += block.candidates_evaluated;
        for (int row = 0; row < block.block_height; ++row) {
            for (int col = 0; col < block.block_width; ++col) {
                const int x = block.block_x + col;
                const int y = block.block_y + row;
                const int rx = x + block.vector.dx;
                const int ry = y + block.vector.dy;
                const int prediction = static_cast<int>(reference.at(rx, ry));
                const int target = static_cast<int>(current.at(x, y));
                const int delta = prediction - target;
                squared_error += static_cast<std::uint64_t>(delta * delta);
            }
        }
    }
    const auto pixels = static_cast<std::uint64_t>(current.width) * static_cast<std::uint64_t>(current.height);
    const double mse = static_cast<double>(squared_error) / static_cast<double>(pixels);
    const double psnr = mse == 0.0 ? std::numeric_limits<double>::infinity() : 10.0 * std::log10((255.0 * 255.0) / mse);
    const double blocks_count = static_cast<double>(blocks.size());
    const double elapsed_seconds = elapsed_ms / 1000.0;

    BenchmarkMetrics metrics;
    metrics.algorithm = algorithm_name(algorithm);
    metrics.width = current.width;
    metrics.height = current.height;
    metrics.block_size = block_size;
    metrics.search_range = search_range;
    metrics.blocks = static_cast<std::uint64_t>(blocks.size());
    metrics.total_candidates = total_candidates;
    metrics.avg_candidates_per_block = blocks_count == 0.0 ? 0.0 : static_cast<double>(total_candidates) / blocks_count;
    metrics.avg_sad_per_pixel = static_cast<double>(total_sad) / static_cast<double>(pixels);
    metrics.mc_psnr_db = psnr;
    metrics.elapsed_ms = elapsed_ms;
    metrics.blocks_per_second = elapsed_seconds > 0.0 ? blocks_count / elapsed_seconds : 0.0;
    return metrics;
}

}  // namespace me
