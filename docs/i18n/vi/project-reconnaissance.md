# Khảo sát dự án dựa trên bằng chứng

`./ai start` quét lại bằng chứng an toàn mỗi session và tạo:

- `.ai/recon/inventory.json`: inventory file manifest/source an toàn.
- `.ai/recon/evidence.json`: checksum và loại bằng chứng.
- `.ai/recon/facts.json`: fact với độ chắc chắn `verified`, `inherited`, `inferred`, `unknown`, `conflicted`.

Công cụ không đọc giá trị `.env`, credential, symlink hoặc đường dẫn ngoài dự án. Dependency chỉ cho biết khả năng tích hợp; Project Brain không khẳng định model/provider STT/TTS nếu chưa có bằng chứng runtime rõ ràng trong `.ai/runtime/model-evidence.json`.
