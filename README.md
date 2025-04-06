# EmRest: A Black-Box Testing Tool for REST APIs

## TODO

- [☑️] 检查 specification 更新是否为最新版（4月6日已检查，均为最新版）
- [ ] 更新 api-exp-scripts

## 修改记录
### 4月6日
- [☑️] 修改```services.py```中GitLab版本至有覆盖率版本，并将密码设置为```MySuperSecretAndSecurePassw0rd!```
- [☑️] 为```services.py```中的proxy文件添加Unique Id
- [☑️] 添加检测覆盖率脚本文件```gitlab_cov.py```在api-suts文件夹内

**EmRest** is a black-box testing tool specifically designed for testing REST APIs. It accepts a Swagger specification file as input and enhances testing for both nominal and exceptional scenarios by
leveraging error messages from HTTP responses.

## Prerequisites

To use EmRest, you’ll need:

- **Linux or macOS**
- **Python >= 3.11**, we use 3.11.11

### Installation Steps

1. **Install Poetry (for dependency management):**

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
2. Load pyenv automatically by appending
# the following to 
# ~/.bash_profile if it exists, otherwise ~/.profile (for login shells)
# and ~/.bashrc (for interactive shells) :

2. Add `export PATH="/$HOME/.local/bin:$PATH"` to your shell configuration file

2. **Install the required dependencies:**

   ```bash
   poetry env use python3.11
   poetry install (will create a virtual environment for the project)
   ```

3. **Install the SpaCy model for constraint extraction:**

   EmRest uses [SpaCy](https://spacy.io/) for natural language processing tasks, such as constraint extraction. To download the required language model, run:

   ```bash
   poetry run python -m spacy download en_core_web_sm
   ```

## Usage Instructions

1. **Navigate to the project directory:**

   ```bash
   cd /path/to/project
   ```

2. **View help information for available commands and options:**

   ```bash
   poetry run python -m src.algorithms --help
   ```

3. **Run the tool with the following command:**

   ```bash
   poetry run python -m src.algorithms --exp_name <name_of_the_sut> --spec_file <path_to_specification> --budget <testing_budget_in_seconds> --output_path <path_to_results> --pict ./lib/pict --server <server_address>
   ```

### Example

To run EmRest on a BookStore API specification:

```bash
poetry run python -m src.algorithms --exp_name test --spec_file ./specifications/BookStoreAPI.json --budget 3600 --output_path ./results --pict ./lib/pict --server http://localhost:8080/v2
```

## Additional Notes

- Ensure that the server specified by the `--server` flag is running and accessible at the given address.
- The `--budget` option defines the total testing time (in seconds), allowing you to control how long the tool runs.
- The results are saved in the directory specified by `--output_path`.
