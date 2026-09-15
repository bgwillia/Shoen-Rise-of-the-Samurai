#pragma once
#include "domain/World.h"
#include <span>
namespace domain {
constexpr std::uint32_t SnapshotVersion = 2;
constexpr std::size_t MaxSnapshotBytes = 16 * 1024 * 1024;
struct DecodeResult { bool ok = false; std::string error; World world; };
// Empty bytes indicate invalid source state. Decoding never changes a live world.
DOMAINCORE_API std::vector<std::uint8_t> EncodeSnapshot(const World&);
DOMAINCORE_API DecodeResult DecodeSnapshot(std::span<const std::uint8_t>);
DOMAINCORE_API Result LoadSnapshot(World&, std::span<const std::uint8_t>);
}
