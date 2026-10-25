#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace me {

struct Image {
    int width{};
    int height{};
    std::vector<std::uint8_t> pixels;

    std::uint8_t at(int x, int y) const;
    std::uint8_t& at(int x, int y);
};

struct MotionVector {
    int dx{};
    int dy{};
};

struct BlockMotion {
    int block_x{};
    int block_y{};
    int block_width{};
    int block_height{};
    MotionVector vector{};
    std::uint64_t sad{};
    std::uint64_t candidates_evaluated{};
};

struct BenchmarkMetrics {
    std::string algorithm;
    int width{};
    int height{};
    int block_size{};
    int search_range{};
    std::uint64_t blocks{};
    std::uint64_t total_candidates{};
    double avg_candidates_per_block{};
    double avg_sad_per_pixel{};
    double mc_psnr_db{};
    double elapsed_ms{};
    double blocks_per_second{};
};

enum class SearchAlgorithm {
    FullSearch,
    ThreeStep,
    Diamond,
    PredictiveDiamond
};

Image load_pgm(const std::string& path);
void save_pgm(const Image& image, const std::string& path);
std::string algorithm_name(SearchAlgorithm algorithm);
SearchAlgorithm parse_algorithm(const std::string& name);
std::vector<BlockMotion> estimate_motion(
    const Image& reference,
    const Image& current,
    int block_size,
    int search_range,
    SearchAlgorithm algorithm);
BenchmarkMetrics benchmark(
    const Image& reference,
    const Image& current,
    int block_size,
    int search_range,
    SearchAlgorithm algorithm);

}  // namespace me
