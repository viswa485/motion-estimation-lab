#include "motion_estimation.hpp"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Options {
    std::string reference;
    std::string current;
    std::string output = "results/benchmark.csv";
    std::string algorithms = "all";
    int block_size = 16;
    int search_range = 8;
};

void print_usage(const char* program) {
    std::cerr << "Usage: " << program << " --reference REF.pgm --current CUR.pgm [options]\n"
              << "Options:\n"
              << "  --algorithm NAME       all|full_search|three_step|diamond|predictive_diamond (default: all)\n"
              << "  --block-size N         Block edge length in pixels (default: 16)\n"
              << "  --search-range N       Search radius in pixels, 0..128 (default: 8)\n"
              << "  --output PATH          CSV destination (default: results/benchmark.csv)\n";
}

Options parse_args(int argc, char** argv) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto require_value = [&](const char* flag) -> std::string {
            if (i + 1 >= argc) throw std::invalid_argument(std::string("Missing value for ") + flag);
            return argv[++i];
        };
        if (arg == "--reference") options.reference = require_value("--reference");
        else if (arg == "--current") options.current = require_value("--current");
        else if (arg == "--algorithm") options.algorithms = require_value("--algorithm");
        else if (arg == "--block-size") options.block_size = std::stoi(require_value("--block-size"));
        else if (arg == "--search-range") options.search_range = std::stoi(require_value("--search-range"));
        else if (arg == "--output") options.output = require_value("--output");
        else if (arg == "--help" || arg == "-h") {
            print_usage(argv[0]);
            std::exit(0);
        } else throw std::invalid_argument("Unknown argument: " + arg);
    }
    if (options.reference.empty() || options.current.empty()) throw std::invalid_argument("--reference and --current are required");
    if (options.block_size <= 0) throw std::invalid_argument("--block-size must be positive");
    if (options.search_range < 0 || options.search_range > 128) throw std::invalid_argument("--search-range must be between 0 and 128");
    return options;
}

std::vector<me::SearchAlgorithm> algorithms_for(const std::string& requested) {
    if (requested == "all") {
        return {me::SearchAlgorithm::FullSearch, me::SearchAlgorithm::ThreeStep,
                me::SearchAlgorithm::Diamond, me::SearchAlgorithm::PredictiveDiamond};
    }
    return {me::parse_algorithm(requested)};
}

void write_csv(const std::string& path, const std::vector<me::BenchmarkMetrics>& metrics) {
    const std::filesystem::path output_path(path);
    if (!output_path.parent_path().empty()) std::filesystem::create_directories(output_path.parent_path());
    std::ofstream output(path);
    if (!output) throw std::runtime_error("Cannot open output CSV: " + path);
    output << "algorithm,width,height,block_size,search_range,blocks,total_candidates,avg_candidates_per_block,avg_sad_per_pixel,mc_psnr_db,elapsed_ms,blocks_per_second\n";
    output << std::setprecision(10);
    for (const auto& m : metrics) {
        output << m.algorithm << ',' << m.width << ',' << m.height << ',' << m.block_size << ',' << m.search_range << ','
               << m.blocks << ',' << m.total_candidates << ',' << m.avg_candidates_per_block << ',' << m.avg_sad_per_pixel << ',';
        if (std::isinf(m.mc_psnr_db)) output << "inf";
        else output << m.mc_psnr_db;
        output << ',' << m.elapsed_ms << ',' << m.blocks_per_second << '\n';
    }
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const Options options = parse_args(argc, argv);
        const me::Image reference = me::load_pgm(options.reference);
        const me::Image current = me::load_pgm(options.current);
        std::vector<me::BenchmarkMetrics> all_metrics;
        for (const auto algorithm : algorithms_for(options.algorithms)) {
            all_metrics.push_back(me::benchmark(reference, current, options.block_size, options.search_range, algorithm));
        }
        write_csv(options.output, all_metrics);
        std::cout << "algorithm,avg_candidates_per_block,avg_sad_per_pixel,mc_psnr_db,elapsed_ms\n";
        std::cout << std::setprecision(6);
        for (const auto& m : all_metrics) {
            std::cout << m.algorithm << ',' << m.avg_candidates_per_block << ',' << m.avg_sad_per_pixel << ',';
            if (std::isinf(m.mc_psnr_db)) std::cout << "inf";
            else std::cout << m.mc_psnr_db;
            std::cout << ',' << m.elapsed_ms << '\n';
        }
        std::cout << "Wrote " << options.output << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 2;
    }
}
