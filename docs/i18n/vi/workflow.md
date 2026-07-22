# Luồng hỗ trợ người dùng

Project Brain tách ngôn ngữ nội bộ khỏi ngôn ngữ giao tiếp với người dùng.

```text
Yêu cầu tiếng Việt của người dùng
        ↓
Agent điều phối chuyển thành input tiếng Anh
        ↓
Agent chuyên môn xử lý bằng hướng dẫn canonical tiếng Anh
        ↓
Kết quả nội bộ được tổng hợp
        ↓
Phản hồi tiếng Việt được gửi cho người dùng
```

## Các bước thay đổi

1. Chạy `./ai start` để nạp trạng thái và đồng bộ adapter.
2. Làm rõ yêu cầu, phạm vi và phần chưa chắc bằng tiếng Việt.
3. Chờ người dùng phê duyệt thay đổi đáng kể.
4. Gửi input tiếng Anh vào agent để phân tích ảnh hưởng hoặc triển khai.
5. Chạy các kiểm tra đã xác minh bằng `./ai check`.
6. Cập nhật knowledge và hồ sơ thay đổi bằng tiếng Anh.
7. Chạy `./ai doctor` trước khi kết thúc.
8. Trả kết quả cuối cùng cho người dùng bằng tiếng Việt.

Không đưa secret, credential hoặc dữ liệu production vào quá trình chuyển ngữ hay prompt gửi agent.
