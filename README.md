# Trace

trace is an PyDM-based application developed at SLAC National Accelerator Laboratory. trace has been built to replace the antiquated StripTool and Java Archive Viewer applications used to plot EPICS data. trace is a flexible, modern application for plotting live data (Channel Access or PV Access), and historical data from the EPICS Archive Appliance. With built in conveniences like an archived PV search, and designed to be easily launched from PyDM widgets, files, or the command line, trace will provide an improved user experience for accelerator staff. Trace is an open-source project.   

For more information and a how to guide on trace see [the project's website](https://slaclab.github.io/trace/)
<p align="center">
  <a href="https://github.com/slaclab/trace/issues/new?assignees=&labels=&template=bug-report.md&title=">Report bug</a>
  ·
  <a href="https://github.com/slaclab/trace/issues/new?template=feature-request.md&labels=request">Request feature</a>
  
</p>

## Contributing to Trace

Thank you for your interest in contributing to **Trace**! Your contributions help make the project better for everyone. Below are the guidelines to ensure a smooth and efficient collaboration.

### How to Contribute

1. **Fork and Clone the Repository**
   - Fork the [Trace repository](https://github.com/slaclab/trace) on GitHub.
   - Clone your fork to your local machine:
     ```bash
     git clone https://github.com/your-username/trace.git
     cd trace
     ```

2. **Set Up Your Development Environment**
   - Install the necessary dependencies:
     ```bash
     pip install -r requirements.txt
     ```

3. **Implement Your Changes**
   - **Code Style:** Follow the [PEP8](https://peps.python.org/pep-0008/) style guide for Python code.
   - **Documentation:** Add docstrings to all new methods and classes using the [NumPy style guide](https://numpydoc.readthedocs.io/en/latest/format.html).
   - **Unit Tests:** Write unit tests for your changes using [Pytest](https://docs.pytest.org/).

4. **Run Tests Locally**
   - Ensure all tests pass before submitting:
     ```bash
     pytest
     ```

5. **Create a Pull Request (PR)**
   - When you feel like your feature is ready to be merged into Trace make a PR and request feedback from the Maintainers. 
   - Provide a descriptive title and detailed description of your changes.

### Pull Request Requirements

To ensure your PR is reviewed efficiently, please adhere to the following:

- **Unit Tests:**
  - Include tests for all new functionality.
  - Ensure tests cover different scenarios and edge cases.

- **Documentation:**
  - All new methods and classes must have comprehensive docstrings.
  - Follow the [NumPy style guide](https://numpydoc.readthedocs.io/en/latest/format.html) for consistency.

- **Code Quality:**
  - Adhere to the [PEP8](https://peps.python.org/pep-0008/) style guide.
  - Ensure your code is clean, well-organized, and free of unnecessary complexity.

### Additional Guidelines
- **Communication:**
  - For significant changes, consider opening an issue to discuss your approach before starting.

### Resources

- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)
- [PEP8 Style Guide](https://peps.python.org/pep-0008/)
- [Pytest Documentation](https://docs.pytest.org/)

### Notes on Contributing to the Documentation

1. **Set Up Your Development Environment**
   - Ensure you are working on your development environment.

2. **Navigate to the Project Directory**
   - Go to the top-level `trace` project directory, which contains the `mkdocs.yml` file.

3. **Make and Test Your Changes Locally**
   - Edit the documentation files as needed.
   - Test your changes locally using MkDocs before submitting a pull request.

---

#### Detailed Steps

1. **Set Up Your Development Environment**
   - Make sure you have all the necessary tools installed (e.g., Python, MkDocs).

2. **Navigate to the Project Directory**
   ```bash
   cd path/to/trace

3. **Install Dependencies**
   ```bash
    pip install -r requirements.txt

4. **Serve the Documentation Locally**
   ```bash
    mkdocs serve

-  Open your browser and go to http://localhost:8000 to preview your changes.

5. **Submit Your Changes**

- After verifying your changes, commit and push them to your forked repository.
-  Create a pull request to submit your updates.

---

If you have any questions or need further assistance, feel free to open an [issue](https://github.com/slaclab/trace/issues) or reach out to the maintainers.