use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

mod ffi {
    #[cfg_attr(target_os = "windows", link(name = "NavyFox.Native", kind = "raw-dylib"))]
    extern "C" {
        // Document lifecycle
        pub fn create_document() -> isize;
        pub fn open_document(path: *const u8, path_len: i32) -> isize;
        pub fn edit_document(path: *const u8, path_len: i32) -> isize;
        pub fn save_document(handle: isize, path: *const u8, path_len: i32) -> i32;
        pub fn dispose(handle: isize);

        // Generic property access
        pub fn get_int(handle: isize, name: *const u8, name_len: i32) -> i32;
        pub fn set_int(handle: isize, name: *const u8, name_len: i32, value: i32) -> i32;
        pub fn get_float(handle: isize, name: *const u8, name_len: i32) -> f64;
        pub fn set_float(handle: isize, name: *const u8, name_len: i32, value: f64) -> i32;
        pub fn get_str(
            handle: isize,
            name: *const u8,
            name_len: i32,
            buf: *mut u8,
            buf_len: i32,
            required: *mut i32,
        ) -> i32;
        pub fn set_str(
            handle: isize,
            name: *const u8,
            name_len: i32,
            value: *const u8,
            value_len: i32,
        ) -> i32;

        // Collection operations
        pub fn get_count(handle: isize, collection: *const u8, collection_len: i32) -> i32;
        pub fn get_child_handle(
            handle: isize,
            collection: *const u8,
            collection_len: i32,
            index: i32,
        ) -> isize;
        pub fn append_child(handle: isize, child_type: *const u8, child_type_len: i32) -> isize;
        pub fn remove_child(handle: isize) -> i32;
        pub fn get_element_type(
            handle: isize,
            buf: *mut u8,
            buf_len: i32,
            required: *mut i32,
        ) -> i32;

        // Special-case constructors
        pub fn add_table(doc_handle: isize, rows: i32, cols: i32) -> isize;
        pub fn add_image(
            para_handle: isize,
            data: *const u8,
            data_len: i32,
            content_type: *const u8,
            content_type_len: i32,
            width_emu: i32,
            height_emu: i32,
        ) -> isize;
        pub fn get_image_data(
            handle: isize,
            buf: *mut u8,
            buf_len: i32,
            required: *mut i32,
        ) -> i32;
    }
}

const BUF_INIT: i32 = 256;

fn native_err(msg: impl Into<String>) -> PyErr {
    PyRuntimeError::new_err(msg.into())
}

// ── Document lifecycle ────────────────────────────────────────────────────────

#[pyfunction]
fn create_document() -> PyResult<isize> {
    let h = unsafe { ffi::create_document() };
    if h == 0 {
        Err(native_err("create_document returned null handle"))
    } else {
        Ok(h)
    }
}

#[pyfunction]
fn open_document(path: &str) -> PyResult<isize> {
    let enc = path.as_bytes();
    let h = unsafe { ffi::open_document(enc.as_ptr(), enc.len() as i32) };
    if h == 0 {
        Err(native_err(format!("open_document failed for {path:?}")))
    } else {
        Ok(h)
    }
}

#[pyfunction]
fn edit_document(path: &str) -> PyResult<isize> {
    let enc = path.as_bytes();
    let h = unsafe { ffi::edit_document(enc.as_ptr(), enc.len() as i32) };
    if h == 0 {
        Err(native_err(format!("edit_document failed for {path:?}")))
    } else {
        Ok(h)
    }
}

#[pyfunction]
fn save_document(handle: isize, path: &str) -> PyResult<()> {
    let enc = path.as_bytes();
    let rc = unsafe { ffi::save_document(handle, enc.as_ptr(), enc.len() as i32) };
    if rc != 0 {
        Err(native_err(format!("save_document failed for {path:?}")))
    } else {
        Ok(())
    }
}

#[pyfunction]
fn dispose(handle: isize) {
    unsafe { ffi::dispose(handle) }
}

// ── Generic property access ───────────────────────────────────────────────────

#[pyfunction]
fn get_int(handle: isize, name: &str) -> i32 {
    let enc = name.as_bytes();
    unsafe { ffi::get_int(handle, enc.as_ptr(), enc.len() as i32) }
}

#[pyfunction]
fn set_int(handle: isize, name: &str, value: i32) -> PyResult<()> {
    let enc = name.as_bytes();
    let rc = unsafe { ffi::set_int(handle, enc.as_ptr(), enc.len() as i32, value) };
    if rc != 0 {
        Err(native_err(format!("set_int({name:?}={value}) failed")))
    } else {
        Ok(())
    }
}

#[pyfunction]
fn get_float(handle: isize, name: &str) -> PyResult<f64> {
    let enc = name.as_bytes();
    let val = unsafe { ffi::get_float(handle, enc.as_ptr(), enc.len() as i32) };
    if val.is_nan() {
        Err(native_err(format!("get_float({name:?}) failed")))
    } else {
        Ok(val)
    }
}

#[pyfunction]
fn set_float(handle: isize, name: &str, value: f64) -> PyResult<()> {
    let enc = name.as_bytes();
    let rc = unsafe { ffi::set_float(handle, enc.as_ptr(), enc.len() as i32, value) };
    if rc != 0 {
        Err(native_err(format!("set_float({name:?}={value}) failed")))
    } else {
        Ok(())
    }
}

#[pyfunction]
fn get_str(handle: isize, name: &str) -> PyResult<String> {
    let enc = name.as_bytes();
    let mut buf_size = BUF_INIT;
    loop {
        let mut buf = vec![0u8; buf_size as usize];
        let mut required: i32 = 0;
        let n = unsafe {
            ffi::get_str(
                handle,
                enc.as_ptr(),
                enc.len() as i32,
                buf.as_mut_ptr(),
                buf_size,
                &mut required,
            )
        };
        if n < 0 {
            return Err(native_err(format!("get_str({name:?}) failed (rc={n})")));
        }
        if n == 0 {
            if required == 0 {
                return Ok(String::new());
            }
            buf_size = required + 1;
            continue;
        }
        buf.truncate(n as usize);
        return Ok(String::from_utf8(buf)
            .map_err(|e| native_err(format!("get_str({name:?}) invalid UTF-8: {e}")))?);
    }
}

#[pyfunction]
fn set_str(handle: isize, name: &str, value: &str) -> PyResult<()> {
    let enc_name = name.as_bytes();
    let enc_val = value.as_bytes();
    let rc = unsafe {
        ffi::set_str(
            handle,
            enc_name.as_ptr(),
            enc_name.len() as i32,
            enc_val.as_ptr(),
            enc_val.len() as i32,
        )
    };
    if rc != 0 {
        Err(native_err(format!("set_str({name:?}) failed")))
    } else {
        Ok(())
    }
}

// ── Collection operations ─────────────────────────────────────────────────────

#[pyfunction]
fn get_count(handle: isize, collection: &str) -> PyResult<i32> {
    let enc = collection.as_bytes();
    let n = unsafe { ffi::get_count(handle, enc.as_ptr(), enc.len() as i32) };
    if n < 0 {
        Err(native_err(format!(
            "get_count({collection:?}) failed (rc={n})"
        )))
    } else {
        Ok(n)
    }
}

#[pyfunction]
fn get_child_handle(handle: isize, collection: &str, index: i32) -> PyResult<isize> {
    let enc = collection.as_bytes();
    let h = unsafe { ffi::get_child_handle(handle, enc.as_ptr(), enc.len() as i32, index) };
    if h == 0 {
        Err(native_err(format!(
            "get_child_handle({collection:?}, {index}) failed"
        )))
    } else {
        Ok(h)
    }
}

#[pyfunction]
fn append_child(handle: isize, child_type: &str) -> PyResult<isize> {
    let enc = child_type.as_bytes();
    let h = unsafe { ffi::append_child(handle, enc.as_ptr(), enc.len() as i32) };
    if h == 0 {
        Err(native_err(format!("append_child({child_type:?}) failed")))
    } else {
        Ok(h)
    }
}

#[pyfunction]
fn remove_child(handle: isize) -> PyResult<()> {
    let rc = unsafe { ffi::remove_child(handle) };
    if rc != 0 {
        Err(native_err("remove_child failed"))
    } else {
        Ok(())
    }
}

#[pyfunction]
fn get_element_type(handle: isize) -> String {
    let mut buf = [0u8; 64];
    let mut required: i32 = 0;
    let n = unsafe { ffi::get_element_type(handle, buf.as_mut_ptr(), 64, &mut required) };
    if n <= 0 {
        return "unknown".to_string();
    }
    String::from_utf8_lossy(&buf[..n as usize]).into_owned()
}

// ── Special-case constructors ─────────────────────────────────────────────────

#[pyfunction]
fn add_table(doc_handle: isize, rows: i32, cols: i32) -> PyResult<isize> {
    let h = unsafe { ffi::add_table(doc_handle, rows, cols) };
    if h == 0 {
        Err(native_err("add_table failed"))
    } else {
        Ok(h)
    }
}

#[pyfunction]
fn add_image(
    parent_handle: isize,
    data: &[u8],
    content_type: &str,
    width_emu: i32,
    height_emu: i32,
) -> PyResult<isize> {
    let enc_ct = content_type.as_bytes();
    let h = unsafe {
        ffi::add_image(
            parent_handle,
            data.as_ptr(),
            data.len() as i32,
            enc_ct.as_ptr(),
            enc_ct.len() as i32,
            width_emu,
            height_emu,
        )
    };
    if h == 0 {
        Err(native_err("add_image failed"))
    } else {
        Ok(h)
    }
}

#[pyfunction]
fn get_image_data(handle: isize) -> PyResult<Vec<u8>> {
    let mut buf_size = 4096i32;
    loop {
        let mut buf = vec![0u8; buf_size as usize];
        let mut required: i32 = 0;
        let n = unsafe {
            ffi::get_image_data(handle, buf.as_mut_ptr(), buf_size, &mut required)
        };
        if n < 0 {
            return Err(native_err("get_image_data failed"));
        }
        if n == 0 {
            if required == 0 {
                return Ok(Vec::new());
            }
            buf_size = required + 1;
            continue;
        }
        buf.truncate(n as usize);
        return Ok(buf);
    }
}

// ─────────────────────────────────────────────────────────────────────────────

#[pymodule]
fn _navyfox(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_document, m)?)?;
    m.add_function(wrap_pyfunction!(open_document, m)?)?;
    m.add_function(wrap_pyfunction!(edit_document, m)?)?;
    m.add_function(wrap_pyfunction!(save_document, m)?)?;
    m.add_function(wrap_pyfunction!(dispose, m)?)?;
    m.add_function(wrap_pyfunction!(get_int, m)?)?;
    m.add_function(wrap_pyfunction!(set_int, m)?)?;
    m.add_function(wrap_pyfunction!(get_float, m)?)?;
    m.add_function(wrap_pyfunction!(set_float, m)?)?;
    m.add_function(wrap_pyfunction!(get_str, m)?)?;
    m.add_function(wrap_pyfunction!(set_str, m)?)?;
    m.add_function(wrap_pyfunction!(get_count, m)?)?;
    m.add_function(wrap_pyfunction!(get_child_handle, m)?)?;
    m.add_function(wrap_pyfunction!(append_child, m)?)?;
    m.add_function(wrap_pyfunction!(remove_child, m)?)?;
    m.add_function(wrap_pyfunction!(get_element_type, m)?)?;
    m.add_function(wrap_pyfunction!(add_table, m)?)?;
    m.add_function(wrap_pyfunction!(add_image, m)?)?;
    m.add_function(wrap_pyfunction!(get_image_data, m)?)?;
    Ok(())
}
