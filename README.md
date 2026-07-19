# English Collocation Profile Online

這個資料夾是 ECP Streamlit demo 的正式交接版。下載到本機後，可以開啟 English Collocation Profile Online，查詢英文搭配詞、CEFR level 與語意標籤。

## 1. Demo 功能

使用者可以：

- 查詢一個 base word，例如 `earn`、`make`、`take`。
- 查看該字常見的 collocation groups。
- 依 CEFR level 篩選，例如只看 A2-B2。
- 依 Guideword / Part of Speech 篩選結果。
- 貼上一小段英文句子，讓 demo 找出句子中出現的 ECP collocations。

畫面中的主要欄位：

- `Collocations`：搭配詞清單，例如 `earn money`、`earn income`。
- `Guideword`：語意標籤。
- `Level`：CEFR / proficiency level。
- `Part of Speech`：搭配詞結構，例如 verb + noun、adjective + noun。

## 2. 檔案說明

請確認資料夾中至少有這兩個檔案：

```text
app.py
ECP_v6_streamlit_clean.csv
```

用途如下：

```text
app.py                    Streamlit demo 主程式
ECP_v6_streamlit_clean.csv ECP demo 用資料
```

`ECP_v6_streamlit_clean.csv` 不要改名，也不要移到其他資料夾。`app.py` 會在同一個資料夾中尋找這個 CSV。

如果資料夾中有 `.devcontainer`，本機執行 demo 時可以忽略。

## 3. 下載到本機

### 用 Git 下載

如果電腦已經安裝 Git，可以在 Terminal / 命令提示字元輸入：

```bash
git clone https://github.com/yahappylemon/ecp-streamlit-demo.git
cd ecp-streamlit-demo
```

### 直接下載 ZIP

如果不熟悉 Git，可以使用瀏覽器打開：

```text
https://github.com/yahappylemon/ecp-streamlit-demo
```

接著點選：

```text
Code -> Download ZIP
```

下載後解壓縮，進入解壓縮後的資料夾。

## 4. 建立虛擬環境

建議使用 virtual environment，避免和電腦中其他 Python 專案互相影響。

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

啟動成功後，命令列前面通常會出現 `(.venv)`。

## 5. 安裝 Streamlit

在 `ecp-streamlit-demo` 資料夾中執行：

```bash
pip install streamlit
```

如果系統找不到 `pip`，可改用：

```bash
python -m pip install streamlit
```

macOS 有時需要使用：

```bash
python3 -m pip install streamlit
```

## 6. 開啟 demo

在同一個資料夾中執行：

```bash
streamlit run app.py
```

成功後，瀏覽器會自動打開 demo。若沒有自動打開，可在瀏覽器輸入 Terminal 顯示的網址，通常是：

```text
http://localhost:8501
```

## 7. 建議測試查詢

第一次開啟後，可以先測試：

```text
earn
make
take
give
knowledge
```

也可以貼入短句，例如：

```text
To strengthen our position, we must develop strategies, build partnerships, assess risks, and make decisions.
```

若畫面出現 collocation groups、CEFR levels 和 guidewords，就表示 demo 已成功啟動。

## 8. 部署到 Streamlit Community Cloud

部署需要兩個檔案放在同一個 GitHub repo：

```text
app.py
ECP_v6_streamlit_clean.csv
```

以下指令中的 `<your-account>` 請換成自己的 GitHub 帳號。

### 8.1 先初始化本機 Git

在目前本機專案的資料夾底下初始化 git：

```bash
git init
git add app.py ECP_v6_streamlit_clean.csv README.md
git commit -m "Initial ECP Streamlit demo"
git branch -M main
```

### 8.2 在 GitHub 建立空 repo

1. 打開：

```text
https://github.com/new
```

2. Repository name 填：

```text
ecp-streamlit-demo
```

3. 選 `Public` 或 `Private`。
4. 不要勾選 `Add a README file`、`.gitignore`、`license`。
5. 按 `Create repository`。

### 8.3 Push 到 GitHub

回到 Terminal，設定 GitHub repo：

```bash
git remote add origin https://github.com/<your-account>/ecp-streamlit-demo.git
```

如果出現 `remote origin already exists`，改用：

```bash
git remote set-url origin https://github.com/<your-account>/ecp-streamlit-demo.git
```

推上去：

```bash
git push -u origin main
```

到 GitHub repo 頁面確認有這兩個檔案：

```text
app.py
ECP_v6_streamlit_clean.csv
```

### 8.4 到 Streamlit Community Cloud 部署

1. 打開：

```text
https://share.streamlit.io
```

2. 用 GitHub 帳號登入。
3. 點 `Create app`。
4. 選 `Yup, I have an app`。
5. 填：

```text
Repository: <your-account>/ecp-streamlit-demo
Branch: main
Main file path: app.py
```

6. 按 `Deploy`。
7. 等部署完成後，打開 Streamlit 產生的網址。

### 8.5 測試線上 app

搜尋：

```text
earn
make
knowledge
```

如果看到 `ECP dataset not found`，回 GitHub 檢查 repo 裡是否有：

```text
app.py
ECP_v6_streamlit_clean.csv
```

### 8.6 之後更新

修改 `app.py` 或 CSV 後：

```bash
git add app.py ECP_v6_streamlit_clean.csv README.md
git commit -m "Update ECP Streamlit demo"
git push
```

Streamlit 會自動重新部署。
