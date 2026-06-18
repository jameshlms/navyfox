use std::{env, path::PathBuf};

fn main() {
    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());
    let repo_root = manifest_dir.parent().unwrap().to_owned();
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());

    let target_os = env::var("CARGO_CFG_TARGET_OS").unwrap();
    let target_arch = env::var("CARGO_CFG_TARGET_ARCH").unwrap();

    let (rid, lib_file) = match (target_os.as_str(), target_arch.as_str()) {
        ("linux", "x86_64")    => ("linux-x64",  "NavyFox.Native.so"),
        ("linux", "aarch64")   => ("linux-arm64", "NavyFox.Native.so"),
        ("windows", "x86_64")  => ("win-x64",    "NavyFox.Native.lib"),
        ("windows", "aarch64") => ("win-arm64",  "NavyFox.Native.lib"),
        ("macos", "aarch64")   => ("osx-arm64",  "NavyFox.Native.dylib"),
        ("macos", "x86_64")    => ("osx-x64",    "NavyFox.Native.dylib"),
        (os, arch) => panic!("navyfox: unsupported platform {os}/{arch}"),
    };

    let lib_dir = repo_root
        .join("src")
        .join("navyfox")
        .join("_libs")
        .join(rid);
    let lib_src = lib_dir.join(lib_file);

    if !lib_src.exists() {
        panic!(
            "navyfox: native binary not found at {}.\n\
             Build with: dotnet publish native/NavyFox.Native -r {rid} -c Release",
            lib_src.display()
        );
    }

    println!("cargo:rerun-if-changed={}", lib_src.display());

    match target_os.as_str() {
        "windows" => {
            // Windows: import library uses the base name without a lib prefix.
            println!("cargo:rustc-link-search=native={}", lib_dir.display());
        }
        _ => {
            // Unix: cargo expects lib-prefixed filenames. Create a symlink in
            // OUT_DIR so cargo:rustc-link-lib=dylib=NavyFox.Native resolves.
            let suffix = if target_os == "macos" { "dylib" } else { "so" };
            let link_name = format!("libNavyFox.Native.{suffix}");
            let link_dst = out_dir.join(&link_name);
            if link_dst.exists() {
                std::fs::remove_file(&link_dst).unwrap();
            }
            // build.rs runs on the host; for our supported platforms host==target.
            #[cfg(unix)]
            std::os::unix::fs::symlink(&lib_src, &link_dst).unwrap();
            println!("cargo:rustc-link-search=native={}", out_dir.display());
            // Absolute rpath for local dev. Distribution will fix this via
            // auditwheel (Linux) or install_name_tool (macOS).
            println!("cargo:rustc-link-arg=-Wl,-rpath,{}", lib_dir.display());
        }
    }

    println!("cargo:rustc-link-lib=dylib=NavyFox.Native");
}
