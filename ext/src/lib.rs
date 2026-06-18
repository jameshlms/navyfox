use pyo3::prelude::*;

extern "C" {
    // Document lifecycle
    fn create_document() -> isize;
    fn open_document(path: *const u8, path_len: i32) -> isize;
    fn edit_document(path: *const u8, path_len: i32) -> isize;
    fn save_document(handle: isize, path: *const u8, path_len: i32) -> i32;
    fn dispose(handle: isize);

    // Generic property access
    fn get_int(handle: isize, name: *const u8, name_len: i32) -> i32;
    fn set_int(handle: isize, name: *const u8, name_len: i32, value: i32) -> i32;
    fn get_float(handle: isize, name: *const u8, name_len: i32) -> f64;
    fn set_float(handle: isize, name: *const u8, name_len: i32, value: f64) -> i32;
    fn get_str(
        handle: isize,
        name: *const u8,
        name_len: i32,
        buf: *mut u8,
        buf_len: i32,
        required: *mut i32,
    ) -> i32;
    fn set_str(
        handle: isize,
        name: *const u8,
        name_len: i32,
        value: *const u8,
        value_len: i32,
    ) -> i32;

    // Collection operations
    fn get_count(handle: isize, collection: *const u8, collection_len: i32) -> i32;
    fn get_child_handle(
        handle: isize,
        collection: *const u8,
        collection_len: i32,
        index: i32,
    ) -> isize;
    fn append_child(handle: isize, child_type: *const u8, child_type_len: i32) -> isize;
    fn remove_child(handle: isize) -> i32;
    fn get_element_type(handle: isize, buf: *mut u8, buf_len: i32, required: *mut i32) -> i32;

    // Special-case constructors
    fn add_table(doc_handle: isize, rows: i32, cols: i32) -> isize;
    fn add_image(
        para_handle: isize,
        data: *const u8,
        data_len: i32,
        content_type: *const u8,
        content_type_len: i32,
        width_emu: i32,
        height_emu: i32,
    ) -> isize;
    fn get_image_data(handle: isize, buf: *mut u8, buf_len: i32, required: *mut i32) -> i32;
}

/// Verify the C# library loads and create_document/dispose round-trips.
/// Temporary — will be replaced by proper wrappers in the next step.
#[pyfunction]
fn _smoke_test() -> PyResult<bool> {
    let handle = unsafe { create_document() };
    if handle == 0 {
        return Err(pyo3::exceptions::PyRuntimeError::new_err(
            "create_document returned null handle",
        ));
    }
    unsafe { dispose(handle) };
    Ok(true)
}

#[pymodule]
fn _navyfox(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(_smoke_test, m)?)?;
    Ok(())
}
