    # SigmaOS-slide-presenter

    Markdown slide presenter

    Part of the **SigmaOS** sovereign operating-system ecosystem — a multi-repository
    distribution modelled on Linux Mint and Omarchy Linux. See the parent
    [`SigmaOS`](https://github.com/AaryanSinghChauhan09/SigmaOS) repository for the
    full component index.

    ## Upstream inspirations
    - https://github.com/omacom/hype

    ## Design principles applied
    - **Abstraction**
- **Separation of Concerns**
- **Fail-Fast**
- **KISS**
- **Least Astonishment**
- **Deterministic Testing**

    ## Usage
    Verbs: `build, themes, next-plan, export-plan`

    ```
    $ sigma-slide build talk.md
$ sigma-slide themes
$ sigma-slide next-plan talk.md --current 1
$ sigma-slide export-plan talk.md --format html

    ```

    ## Build & test
    ```
    make build
    make test
    ```

    ## Licence
    GNU General Public License v3.0 (FOSS).
