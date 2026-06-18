use pyo3::prelude::*;

#[pymodule]
fn _navyfox(_py: Python<'_>, _m: &Bound<'_, PyModule>) -> PyResult<()> {
    Ok(())
}
