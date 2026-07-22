# Project Brain

> **Tài liệu tiếng Việt:** Đây là entry point dành cho người dùng. Hướng dẫn canonical/internal trong `.ai/` được viết bằng tiếng Anh. Xem thêm lớp i18n tại [`docs/i18n/vi/`](docs/i18n/vi/README.md).

Project Brain là bộ khung quản trị tri thức và quy trình cho các agent hỗ trợ phát triển phần mềm. Nó giúp Claude Code, Codex, Kiro, Hermes và adapter generic làm việc nhất quán qua nhiều session, dựa trên một nguồn thông tin chuẩn trong `.ai/`. Chọn adapter khi cài bằng `--target claude|codex|kiro|hermes|generic|all`; chạy `./ai discover` để xem verified/inferred/unknown/conflicted. Lệnh noninteractive không tự xác nhận provider/model STT/TTS.

> **Trạng thái hiện tại:** Repository mới có framework Project Brain; chưa có source code ứng dụng nghiệp vụ. Tên sản phẩm, mục đích nghiệp vụ, technology stack, database, authentication, API và deployment vẫn **chưa xác minh**.

## Project Brain làm gì?

Framework này hỗ trợ đội ngũ:

- Lưu thông tin chuẩn của dự án và các quyết định đã xác nhận.
- Tạo tóm tắt session để agent bắt đầu đúng bối cảnh.
- Tiếp nhận và làm rõ yêu cầu trước khi thay đổi.
- Xin phê duyệt trước các thay đổi đáng kể.
- Phân tích ảnh hưởng tới code, dữ liệu, bảo mật, test, tài liệu và vận hành.
- Đồng bộ hướng dẫn giữa Claude Code và Codex.
- Phát hiện workflow có thể tái sử dụng, tạo skill candidate và chỉ promote sau approval riêng.
- Trình proposal skill bằng tiếng Việt nhưng lưu canonical `SKILL.md` bằng tiếng Anh.
- Chạy các quality gate và kiểm tra bảo mật ở mức repository.
- Giữ rõ ràng ranh giới giữa thông tin đã xác minh và phần chưa biết.

Framework **không tự suy đoán chức năng ứng dụng**, không chứa source code nghiệp vụ trong trạng thái hiện tại và không thay thế quy trình phê duyệt production.

## Quy ước ngôn ngữ

```text
Input gửi agent: English
Canonical/internal instructions: English
Output trả về người dùng: Tiếng Việt
```

Lệnh, path, schema key và code identifier được giữ nguyên. Nội dung tiếng Việt dành cho người dùng được duy trì tại `README.md` và `docs/i18n/vi/`; nếu có sai khác về hành vi agent, canonical English trong `.ai/` là nguồn quyết định.

## Luồng hỗ trợ người dùng

Một yêu cầu thay đổi đi qua các bước sau:

```text
Người dùng đưa yêu cầu
        ↓
Làm rõ mục tiêu, phạm vi và điểm chưa chắc
        ↓
Người dùng phê duyệt
        ↓
Phân tích ảnh hưởng
        ↓
Triển khai thay đổi đã được duyệt
        ↓
Kiểm chứng build/test/runtime phù hợp
        ↓
Cập nhật tri thức và quyết định của dự án
        ↓
Quality gate cuối cùng
```

### 1. Khởi động session

```bash
./ai start
```

Lệnh này kiểm tra nhanh framework, đồng bộ adapter, quét metadata an toàn và tạo session brief.

### 2. Tiếp nhận thay đổi

Agent ghi nhận yêu cầu, giải thích bằng ngôn ngữ đời thường và nêu:

- Hiện trạng.
- Kết quả mong muốn.
- Người hoặc quy trình bị ảnh hưởng.
- Phần có thể chỉnh.
- Những điều chưa chắc.

Thay đổi đáng kể chỉ được thực hiện sau khi người dùng xác nhận phạm vi.

### 3. Phân tích ảnh hưởng

Agent xác định file, module, test, tài liệu, dữ liệu, tích hợp và rủi ro liên quan. Các khu vực rủi ro cao gồm database migration, authentication, authorization, data deletion, API contract, production dependency, infrastructure và external service cost.

### 4. Triển khai và kiểm chứng

Sau approval, agent mới triển khai trong phạm vi đã duyệt, chạy kiểm tra phù hợp và cập nhật hồ sơ thay đổi. Không chỉnh trực tiếp file generated.

## Cấu trúc repository

```text
.ai/
├── knowledge/       # Tri thức canonical của dự án
├── policy/          # Quy tắc cốt lõi, approval và bảo mật
├── skills/          # Skill canonical cho quy trình agent
├── changes/         # Hồ sơ request, approval, impact và verification
├── generated/       # Context tự sinh, có thể tái tạo
├── runtime/         # Trạng thái tạm thời, không phải nguồn tri thức
└── scripts/         # CLI và script quản trị

.agents/skills/      # Adapter skill cho Codex
.claude/skills/      # Adapter skill cho Claude Code
AGENTS.md            # Adapter hướng dẫn cho Codex
CLAUDE.md            # Adapter hướng dẫn cho Claude Code
ai                  # Launcher Linux/macOS
ai.cmd              # Launcher Windows
```

Nguồn sự thật nằm trong `.ai/` và được viết bằng tiếng Anh; các adapter và nội dung generated được đồng bộ hoặc tái tạo từ nguồn đó. Tài liệu tiếng Việt tại `docs/i18n/vi/` là lớp i18n dành cho người dùng.

## Các lệnh thường dùng

### Khởi động và xem trạng thái

```bash
./ai start
./ai status
./ai brief
```

### Kiểm tra chất lượng

```bash
./ai check
./ai doctor
./ai close
```

- `./ai check`: chạy các lệnh build/test/lint/format đã được khai báo và kiểm tra các điều kiện của change record.
- `./ai doctor`: kiểm tra sức khỏe framework, file bắt buộc, schema, adapter, symlink, context và secret pattern.
- `./ai close`: quality gate trước khi kết thúc công việc.

### Đồng bộ và chạy agent

```bash
./ai sync
./ai claude
./ai codex
```

`./ai claude` và `./ai codex` khởi động Project Brain trước, sau đó gọi CLI tương ứng nếu đã được cài trong môi trường.

### Skill candidate có approval riêng

Sau khi một workflow đã được kiểm chứng, agent có thể đề xuất lưu thành skill project-local. Việc duyệt task nghiệp vụ không đồng nghĩa với duyệt skill. Trước khi tạo hoặc cập nhật skill, agent phải trình proposal đầy đủ bằng tiếng Việt; canonical `SKILL.md` luôn viết bằng tiếng Anh.

```bash
# Xem proposal tiếng Việt từ candidate draft.
./ai skill-proposal .ai/skill-candidates/<candidate-id>/candidate.json

# Chỉ chạy sau khi candidate có approval riêng, đúng candidate_id và content SHA-256.
./ai skill-promote .ai/skill-candidates/<candidate-id>/candidate.json
```

Candidate draft nằm dưới `.ai/skill-candidates/`; chỉ candidate đã được approval riêng mới được promote vào `.ai/skills/`. Workflow này không sửa global Hermes skills, memory, profiles hoặc config.

## Cài đặt và kiểm thử hiện tại

Framework hiện không có production dependency. Môi trường cần có Python 3 và shell trên Linux/macOS; Windows có thể dùng `ai.cmd` khi Python nằm trong `PATH`.

### Cài vào repository hiện có và chọn agent platform

Project Brain chỉ ghi trong thư mục dự án được chọn (`--directory`, mặc định là thư mục hiện tại). Không cài package, service, cấu hình global hoặc ghi vào `~/.hermes`. File dự án đang tồn tại được giữ nguyên.

Các target được hỗ trợ:

- `claude`: `CLAUDE.md`, `.claude/skills/`
- `codex`: `AGENTS.md`, `.agents/skills/`, `.codex/` nếu dự án có sẵn
- `kiro`: `.kiro/steering/`
- `hermes`: `.ai/adapters/hermes/` — project-local, không sửa Hermes global
- `generic`: `.ai/adapters/generic/`
- `all`: tất cả adapter trên
- `both`: alias tương thích cũ của `claude + codex`

### Trạng thái phát hành

Tài liệu này mô tả bản `1.0.9` đã build và verify local. Release public mới nhất hiện là `1.0.8`; không sử dụng URL `releases/download/1.0.9/...` cho đến khi release 1.0.9 được publish cùng `install.sh` và archive đã kiểm tra checksum.

Để thử bản 1.0.9 từ source local đã review:

```bash
# Kiểm tra không ghi file.
./install.sh --dry-run --directory "$PWD" --target all

# Cài tất cả adapter.
./install.sh --directory "$PWD" --target all --version 1.0.9
```

Cài một platform riêng từ source local:

```bash
./install.sh --directory "$PWD" --target claude --version 1.0.9
./install.sh --directory "$PWD" --target codex --version 1.0.9
./install.sh --directory "$PWD" --target kiro --version 1.0.9
./install.sh --directory "$PWD" --target hermes --version 1.0.9
./install.sh --directory "$PWD" --target generic --version 1.0.9
```

### Sau khi cài: discover dự án, không đoán model

`install.sh` chỉ cài harness và file adapter. Trong dự án, chạy:

```bash
./ai discover
```

`discover` phân loại thông tin thành:

- `verified`: có bằng chứng trực tiếp từ project hoặc user đã xác nhận;
- `inferred`: dấu hiệu từ dependency/config, chưa đủ để kết luận runtime;
- `unknown`: chưa có bằng chứng;
- `conflicted`: các nguồn không thống nhất.

Đặc biệt, Project Brain **không tự kết luận** STT/TTS provider hoặc model chỉ vì thấy `whisper`, `faster-whisper`, `MiniMax`, `OpenAI` trong dependency. Khi chạy trong terminal interactive, `./ai discover` sẽ hỏi các giá trị còn `unknown`; nhấn Enter để giữ unknown nếu chưa chắc.

Sau đó tạo context cho session mới:

```bash
./ai start
./ai doctor
```

`./ai start` re-scan evidence an toàn ở mỗi session mới. Nội dung canonical nằm trong `.ai/`; adapter chỉ là bản render cho từng platform.

### Kế thừa agent cũ

```bash
./ai onboard
# Xem .ai/imports/report.md rồi mới quyết định:
./ai adopt
```

`onboard` chỉ đọc file hướng dẫn project-local được hỗ trợ như `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.agents/skills`, Cursor và Copilot rules. Nó không đọc `.env`, credential, `.git`, symlink hoặc nội dung có secret pattern. `adopt` là opt-in và không ghi đè nội dung legacy.

### Cài từ source local hoặc gỡ cài đặt

```bash
./install.sh --dry-run --target all
./install.sh --target all --version 1.0.9
./install.sh --uninstall
```

Bootstrap public tải archive `project-brain-1.0.9.tar.gz` qua HTTPS và kiểm tra SHA-256 được ghim trong `install.sh` trước khi giải nén. Release `1.0.9` là bản local đã build và verify; chỉ publish sau khi asset public được cập nhật tương ứng.

Chạy test của framework:

```bash
python3 -m unittest discover -s .ai/tests -p 'test_*.py'
```

## Nguyên tắc an toàn

- Không đọc hoặc đưa secret, credential, private key hay dữ liệu production vào context.
- Không tự mở rộng phạm vi sau khi được duyệt.
- Mọi thông tin chưa có bằng chứng phải ghi là `chưa xác minh`.
- Kiểm tra input tại các ranh giới hệ thống khi source code ứng dụng xuất hiện.
- Không hardcode secret.
- Không coi file generated là nguồn chỉnh sửa chính.
- Các thay đổi có rủi ro cao phải có phê duyệt phù hợp trước khi triển khai.

## Trạng thái và giới hạn xác minh

Đã xác minh:

- Framework Project Brain trong `.ai/` đã được thiết lập và harden.
- Các kiểm tra bắt buộc của framework đang PASS.
- Test framework đã xác minh bằng `python3 -m unittest discover -s .ai/tests -p 'test_*.py'`.

Chưa xác minh:

- Tên và mục đích của ứng dụng nghiệp vụ.
- Source code, ngôn ngữ và framework ứng dụng.
- Database, authentication, authorization và API.
- Tích hợp bên ngoài, deployment và CI/CD.
- Lệnh build, lint và format của ứng dụng.

Khi source code ứng dụng xuất hiện, cần cập nhật `.ai/project.json` và các tài liệu trong `.ai/knowledge/` dựa trên bằng chứng thực tế, sau đó cập nhật README này.

## Tài liệu liên quan

- [Project brief](.ai/knowledge/project-brief.md)
- [Kiến trúc](.ai/knowledge/architecture.md)
- [Quy tắc nghiệp vụ](.ai/knowledge/business-rules.md)
- [Vận hành](.ai/knowledge/operations.md)
- [Trạng thái hiện tại](.ai/knowledge/active-state.md)
- [Các quyết định](.ai/knowledge/decisions.md)
- [Chính sách phê duyệt](.ai/policy/approvals.md)
- [Chính sách bảo mật](.ai/policy/security.md)
- [Tài liệu i18n tiếng Việt](docs/i18n/vi/README.md)
- [Luồng song ngữ cho người dùng](docs/i18n/vi/workflow.md)
