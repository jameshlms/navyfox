# Changelog

All notable changes to NavyFox will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project scaffold.
- C# Native AOT shared library (`NavyFox.Native`) targeting net9.0 with
  DocumentFormat.OpenXml 3.5.1.
- Python package `navyfox` with `Document`, `Paragraph`, `Table`, and `Cell`
  classes.
- Platform-aware lazy binary loader (`navyfox._native.loader`).
- CFFI bindings matching the C# `[UnmanagedCallersOnly]` exports.
- `check_struct_layouts.py` CI guard for FFI struct annotations.
- GitHub Actions workflows: `build-native`, `ci`, `release`.

## [0.1.1] — 2026-06-18

### Fixed

- Release workflow: add `hatchling` to build tool installs so `python -m build --no-isolation` can find the build backend.

## [0.1.0] — Unreleased
