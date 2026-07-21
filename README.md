# Project Brain

[![Release](https://img.shields.io/github/v/release/Hieupt1904/project-brain-installer)](https://github.com/Hieupt1904/project-brain-installer/releases)
[![Tests](https://img.shields.io/badge/tests-76%20passed-brightgreen)](https://github.com/Hieupt1904/project-brain-installer/releases/tag/1.0.5)

> Bộ khung quản trị tri thức và quy trình cho AI Agent trong từng repository.

Project Brain biến một project bình thường thành project có **bộ nhớ dự án, luật làm việc, quy trình approval và quality gate** cho Claude Code, Codex, Hermes và các agent khác.

---

## 📖 Project Brain là gì?

Khi dùng Claude Code, Codex hoặc Hermes trong một project, agent thường:

- Không nhớ kiến trúc, quyết định hay quy tắc của dự án.
- Tự ý sửa code mà không xin ý kiến.
- Đọc nhầm secret, credential hoặc dữ liệu nhạy cảm.
- Lặp lại sai lầm từ các session trước.

**Project Brain giải quyết bằng cách:**

- Lưu tri thức chuẩn của dự án trong `.ai/`.
- Tạo session brief để agent bắt đầu đúng bối cảnh.
- Yêu cầu approval trước các thay đổi đáng kể.
- Quét secret, symlink và path traversal.
- Phát hiện workflow tái sử dụng → đề xuất tạo skill (có approval riêng).
- Chạy quality gate trước khi kết thúc.

---

## 🚀 Cài đặt

### Yêu cầu

- Python 3
- `curl` (khi cài từ GitHub Release)
- Linux/macOS (Windows dùng `ai.cmd`)

### Cài vào project của bạn

```bash
# Đứng trong thư mục gốc của project cần cài
cd /path/to/your-project

# Tải installer
curl -fsSL https://github.com/Hieupt1904/project-brain-installer/releases/download/1.0.5/install.sh \
  -o /tmp/project-brain-install.sh

# Xem trước những gì sẽ được cài (không ghi gì)
sh /tmp/project-brain-install.sh --dry-run --directory "$PWD" --target both

# Cài đặt
sh /tmp/project-brain-install.sh --directory "$PWD" --target both --version 1.0.5
```

### Sau khi cài

```bash
# Khởi tạo inventory cho hướng dẫn AI cũ (nếu có)
./ai onboard

# Tích hợp Project Brain mà không ghi đè nội dung cũ
./ai adopt

# Khởi động session
./ai start
```

### Kiểm tra checksum (tùy chọn)

```bash
grep ARCHIVE_SHA256 /tmp/project-brain-install.sh
sha256sum /tmp/project-brain-install.sh
```

Installer luôn ghim SHA-256 của archive trong script. Nếu archive bị sửa, installer sẽ tự động từ chối.

---

## 🎯 Chọn adapter

| `--target` | Cài cho | File tạo |
|---|---|---|
| `claude` | Claude Code | `CLAUDE.md`, `.claude/` |
| `codex` | Codex | `AGENTS.md`, `.agents/` |
| `both` | Cả hai | Tất cả file ở trên |

```bash
# Chỉ Claude Code
sh /tmp/project-brain-install.sh --target claude

# Chỉ Codex
sh /tmp/project-brain-install.sh --target codex

# Cả hai (mặc định)
sh /tmp/project-brain-install.sh --target both
```

---

## 📁 Cấu trúc sau khi cài

```text
your-project/
├── .ai/
│   ├── project.json          # Mô tả dự án, stack, test command
│   ├── knowledge/            # Tri thức canonical (English)
│   ├── policy/               # Quy tắc approval, bảo mật
│   ├── skills/               # Skill canonical (English)
│   ├── changes/              # Hồ sơ thay đổi
│   ├── generated/            # Context tự sinh (session brief, repo map)
│   ├── runtime/              # Trạng thái tạm thời
│   ├── recon/                # Kết quả khảo sát repository
│   ├── imports/              # Inventory hướng dẫn AI cũ
│   ├── scripts/              # CLI và script quản trị
│   └── tests/                # Test framework
│
├── .claude/                   # Adapter Claude Code
├── .agents/                   # Adapter Codex
├── CLAUDE.md
├── AGENTS.md
├── ai                         # Launcher Linux/macOS
├── ai.cmd                     # Launcher Windows
└── install.sh
```

> Nguồn sự thật nằm trong `.ai/` (English). Các adapter được sinh ra từ nguồn này.

---

## 🔧 Các lệnh

### Khởi động và trạng thái

| Lệnh | Chức năng |
|---|---|
| `./ai start` | Khảo sát project, tạo session brief, đồng bộ adapter |
| `./ai status` | Xem trạng thái hiện tại |
| `./ai brief` | Tạo session brief |

### Kiểm tra chất lượng

| Lệnh | Chức năng |
|---|---|
| `./ai check` | Chạy build/test/lint/format + kiểm tra change record + doc impact |
| `./ai doctor` | Kiểm tra file bắt buộc, schema, adapter, symlink, secret, context |
| `./ai close` | Quality gate cuối cùng trước khi kết thúc |

### Đồng bộ và chạy agent

| Lệnh | Chức năng |
|---|---|
| `./ai sync` | Đồng bộ canonical skills → adapter Claude/Codex |
| `./ai claude` | Chạy `./ai start` rồi gọi Claude Code |
| `./ai codex` | Chạy `./ai start` rồi gọi Codex |

### Skill candidate (mới ở 1.0.5)

| Lệnh | Chức năng |
|---|---|
| `./ai skill-proposal <path>` | Hiển thị proposal tiếng Việt từ candidate draft |
| `./ai skill-promote <path>` | Promote skill (chỉ khi có approval riêng) |

### Khác

| Lệnh | Chức năng |
|---|---|
| `./ai onboard` | Lập inventory an toàn cho hướng dẫn AI cũ |
| `./ai adopt` | Tích hợp Project Brain mà không ghi đè file cũ |

---

## 🔄 Luồng vận hành

```text
Mở session
    │
    ├── ./ai start
    │       ├── Quét lại source evidence
    │       ├── Tạo recon inventory + checksum
    │       ├── Tạo session brief
    │       ├── Đồng bộ adapter
    │       └── Chạy doctor nhanh
    │
    ├── Agent đọc session brief
    │
    └── User đưa yêu cầu
            │
            ▼
    Làm rõ yêu cầu (tiếng Việt)
            │
            ▼
    User approval
            │
            ▼
    Tạo change record
            │
            ├── request.md
            ├── approval.md
            ├── scope.json
            └── impact.md
            │
            ▼
    Triển khai đúng scope
            │
            ▼
    ./ai check
            │
            ▼
    ./ai close
```

---

## 🧠 Skill Candidate Lifecycle (1.0.5)

Project Brain 1.0.5 bổ sung workflow tự động phát hiện skill phù hợp.

```text
Workflow đã được verify
        ↓
Đánh giá: có tái sử dụng được không?
        ↓
Kiểm tra skill trùng lặp
        ↓
Tạo candidate draft
        ↓
Trình proposal đầy đủ bằng TIẾNG VIỆT
        ↓
User approval RIÊNG
        ↓
Kiểm tra candidate ID + SHA-256
        ↓
Promote SKILL.md bằng TIẾNG ANH
        ↓
./ai sync + ./ai doctor
```

### Quy tắc

- Proposal và approval **luôn bằng tiếng Việt**.
- Canonical `SKILL.md` **luôn bằng tiếng Anh**.
- Approval tạo skill **riêng biệt** với approval task nghiệp vụ.
- Skill chỉ nằm trong `.ai/skills/` của project hiện tại.
- Không sửa global Hermes, memory, profiles hoặc config.

---

## ⬆️ Nâng cấp

```bash
# Xem những file sẽ được cập nhật
sh /tmp/project-brain-install.sh --dry-run --directory "$PWD" --target both --version 1.0.5

# Nâng cấp
sh /tmp/project-brain-install.sh --directory "$PWD" --target both --version 1.0.5
```

- Installer chỉ ghi đè file do Project Brain quản lý và chưa bị sửa.
- File đã chỉnh thủ công sẽ được giữ nguyên.
- File mới sẽ được thêm vào manifest.

---

## 🗑️ Gỡ cài đặt

```bash
# Xem những gì sẽ bị xoá
sh /tmp/project-brain-install.sh --uninstall --dry-run

# Gỡ
sh /tmp/project-brain-install.sh --uninstall
```

- Chỉ xoá file trong `.ecc/install-manifest.json`.
- Chỉ xoá nếu checksum khớp lúc cài.
- File đã bị sửa sẽ được giữ lại.
- Không cần mạng.

---

## 🛡️ Bảo mật

Project Brain thực thi các nguyên tắc:

- **Không đọc** `.env`, credential, private key, `.git`, symlink.
- **Không đưa** secret vào context hoặc generated file.
- **Kiểm tra** secret pattern, symlink, path traversal trước mỗi thao tác.
- **Từ chối** command chứa shell operator hoặc executable nguy hiểm.
- **Yêu cầu approval** cho database migration, auth, data deletion, API contract, production dependency, infrastructure và skill creation.
- **File generated** không được chỉnh trực tiếp; chỉ sửa canonical và chạy `./ai sync`.

---

## 🧪 Kiểm thử

```bash
python3 -m unittest discover -s .ai/tests -p 'test_*.py'
```

Kết quả bản 1.0.5:

```text
Ran 76 tests in 0.59s
OK
```

---

## 🔗 Dùng với Hermes Agent

Hermes đọc `AGENTS.md` trong working directory, nên sau khi cài Project Brain:

```bash
cd /path/to/your-project
./ai start
hermes
```

Hermes sẽ dùng được:

- `AGENTS.md` — hướng dẫn đọc Project Brain.
- `.ai/generated/session-brief.md` — bối cảnh dự án.
- `.ai/knowledge/` — kiến trúc, business rules.
- `.ai/policy/` — approval và bảo mật.
- `.ai/skills/` — skill canonical.
- `./ai check`, `./ai doctor`, `./ai close`.

---

## 📋 Phiên bản

| Phiên bản | Tính năng chính |
|---|---|
| **1.0.5** | Skill candidate lifecycle, approval-gated, CLI mới |
| **1.0.4** | Target-aware post-install, fresh-install hardening |
| **1.0.3** | Atomic symlink-safe manifest, malformed adopt marker fix |
| **1.0.2** | External curl installer, SHA-256 pinned archive |
| **1.0.1** | GitHub Release distribution |
| **1.0.0** | Framework ban đầu |

> Chính sách không thay thế: asset đã publish không bao giờ bị sửa. Bản sửa lỗi luôn publish version mới.

---

## ❓ Troubleshooting

### Installer báo "archive checksum mismatch"

Archive đã bị thay đổi sau khi publish. Tải lại installer từ GitHub Release mới nhất:

```bash
curl -fsSL https://github.com/Hieupt1904/project-brain-installer/releases/download/1.0.5/install.sh \
  -o /tmp/project-brain-install.sh
```

### `./ai doctor` báo FAIL

```bash
./ai sync
./ai doctor
```

Nếu vẫn FAIL, đọc thông báo cụ thể trong output — mỗi check có kèm hướng dẫn sửa.

### Installer báo "conflicts found"

Project đã có `CLAUDE.md`, `AGENTS.md` hoặc `.ai/`. Installer không ghi đè. Chạy:

```bash
./ai onboard
./ai adopt
```

### Skill promote báo "content hash does not match"

Canonical `SKILL.md` đã đổi sau approval. Trình lại proposal tiếng Việt và xin approval mới.

---

## 📄 Giấy phép

MIT

---

## 🔗 Links

- **Releases:** https://github.com/Hieupt1904/project-brain-installer/releases
- **Latest:** [1.0.5](https://github.com/Hieupt1904/project-brain-installer/releases/tag/1.0.5)
- **Installer:** `https://github.com/Hieupt1904/project-brain-installer/releases/download/1.0.5/install.sh`
