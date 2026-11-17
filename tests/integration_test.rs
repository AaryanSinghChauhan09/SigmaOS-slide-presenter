// Integration test for SigmaOS-slide-presenter
// Verifies the crate builds and links as a dependency.
#![allow(unused_imports)]

use sigmaos_slide_presenter as _;

#[test]
fn crate_links_and_runs() {
    assert_eq!(2 + 2, 4);
}
