#include "motion_estimation.hpp"

#include <filesystem>
#include <fstream>
#include <cstdint>
#include <iostream>
#include <stdexcept>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
me::Image make_reference(int width, int height) {
    me::Image image;
    image.width = width;
    image.height = height;
    image.pixels.resize(static_cast<std::size_t>(width) * static_cast<std::size_t>(height));
    std::uint32_t state = 123456789U;
    for (auto& pixel : image.pixels) {
        state = 1664525U * state + 1013904223U;
        pixel = static_cast<std::uint8_t>((state >> 16U) & 0xFFU);
    }
    return image;
}
me::Image translated(const me::Image& reference, int dx, int dy) {
    me::Image current = reference;
    for (int y = 0; y < current.height; ++y) for (int x = 0; x < current.width; ++x) {
        const int rx = x + dx, ry = y + dy;
        current.at(x, y) = (rx >= 0 && ry >= 0 && rx < reference.width && ry < reference.height)
            ? reference.at(rx, ry) : 0;
    }
    return current;
}
void test_full_search_finds_translation() {
    const auto reference = make_reference(64, 48);
    const auto current = translated(reference, 3, -2);
    const auto blocks = me::estimate_motion(reference, current, 8, 5, me::SearchAlgorithm::FullSearch);
    const auto& center = blocks.at(2U * 8U + 3U);
    require(center.vector.dx == 3, "Full search did not recover dx=3");
    require(center.vector.dy == -2, "Full search did not recover dy=-2");
    require(center.sad == 0U, "Translated center block should have zero SAD");
}
void test_algorithms_return_valid_vectors() {
    const auto reference = make_reference(40, 32);
    const auto current = translated(reference, 2, 1);
    for (const auto algorithm : {me::SearchAlgorithm::ThreeStep, me::SearchAlgorithm::Diamond,
                                 me::SearchAlgorithm::PredictiveDiamond}) {
        const auto blocks = me::estimate_motion(reference, current, 8, 4, algorithm);
        require(!blocks.empty(), "Search returned no blocks");
        for (const auto& block : blocks) {
            require(block.vector.dx >= -4 && block.vector.dx <= 4, "Motion vector dx escaped search range");
            require(block.vector.dy >= -4 && block.vector.dy <= 4, "Motion vector dy escaped search range");
            require(block.candidates_evaluated > 0U, "Search did not count any candidates");
        }
    }
}
void test_ascii_pgm_accepts_zero_pixels() {
    const auto path = std::filesystem::temp_directory_path() / "motion-estimation-lab-test.pgm";
    { std::ofstream out(path); out << "P2\n2 2\n255\n0 10 255 4\n"; }
    const auto image = me::load_pgm(path.string());
    require(image.width == 2 && image.height == 2, "ASCII PGM dimensions parsed incorrectly");
    require(image.at(0, 0) == 0U && image.at(1, 0) == 10U && image.at(0, 1) == 255U,
            "ASCII PGM pixel values parsed incorrectly");
    std::filesystem::remove(path);
}
void test_mismatched_dimensions_fail() {
    const auto reference = make_reference(16, 16);
    const auto current = make_reference(15, 16);
    bool threw = false;
    try { (void)me::estimate_motion(reference, current, 8, 2, me::SearchAlgorithm::FullSearch); }
    catch (const std::invalid_argument&) { threw = true; }
    require(threw, "Mismatched frame dimensions should be rejected");
}
}
int main() {
    test_full_search_finds_translation();
    test_algorithms_return_valid_vectors();
    test_mismatched_dimensions_fail();
    test_ascii_pgm_accepts_zero_pixels();
    std::cout << "All motion-estimation unit tests passed.\n";
    return 0;
}
