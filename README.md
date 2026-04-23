# 🗄️ Hệ thống Quản lý Cơ sở Dữ liệu Câu Hỏi
## 📌 Tổng quan dự án

Hệ thống quản lý và xử lý dữ liệu câu hỏi trắc nghiệm được xây dựng trên **nhiều cơ sở dữ liệu SQL Server riêng biệt**, với cơ chế đồng bộ dữ liệu tự động thông qua **Trigger và logic SQL**.

Dự án tập trung vào:
- Thiết kế cơ sở dữ liệu quan hệ
- Quản lý luồng dữ liệu giữa nhiều database
- Tự động đồng bộ dữ liệu bằng Trigger
- Kiểm soát trùng lặp và kiểm duyệt dữ liệu

---

## 🎯 Chức năng chính

- Quản lý câu hỏi trắc nghiệm  
- Quản lý thông tin mô tả (Mota)  
- Phân luồng dữ liệu qua 3 nguồn dữ liệu:
  - DLTT (dữ liệu thu thập trực tuyến từ web)
  - DLTS (dữ liệu tạo sinh từ AI)
  - DLTC (dữ liệu nhập thủ công)
- Đồng bộ dữ liệu về CSDLNC (cơ sở dữ liệu trung tâm)  
- Kiểm tra trùng lặp câu hỏi tự động  
- Tự động insert / update / delete giữa các database thông qua Trigger SQL  

---

## 🧠 Phần tôi phụ trách

- Thiết kế toàn bộ database schema
- Thiết kế luồng dữ liệu giữa các database
- Viết toàn bộ SQL script
- Xây dựng hệ thống Trigger:
  - Đồng bộ dữ liệu giữa các database
  - Kiểm tra trùng câu hỏi
  - Kiểm duyệt theo trạng thái dữ liệu
  - MERGE dữ liệu về CSDLNC
- Xử lý logic toàn bộ CRUD bằng SQL

---

## 🧩 Kiến trúc hệ thống

### 📌 Mô hình hệ thống
## 📊 Quy trình thu thập và tạo dữ liệu

<table>
  <tr>
    <th>Thu thập dữ liệu từ web</th>
    <th>Tạo sinh dữ liệu</th>
    <th>Thu thập thủ công</th>
  </tr>

  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/3a3e7c74-2aca-47ff-a8d7-7b576240a110" width="300"/>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/a744eb84-b318-45c6-ae4f-3c8f19d9103b" width="300"/>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/f8e7079b-51c9-4844-b1cd-0b8589e0503a" width="300"/>
    </td>
  </tr>
</table>

---


### 📌 Thiết kế cơ sở dữ liệu
  <img width="865" height="444" alt="image" src="https://github.com/user-attachments/assets/67e87ad8-656c-4fcc-bb25-5dce955bab11" />


## ⚙️ Cơ chế đồng bộ dữ liệu

Hệ thống sử dụng Trigger để:

- Tự động đẩy dữ liệu từ DLTT / DLTS / DLTC về CSDLNC
- Kiểm tra dữ liệu trùng trước khi insert
- Cập nhật dữ liệu khi có thay đổi
- Xóa dữ liệu đồng bộ khi delete

---

## 🧾 Một số trigger tiêu biểu

- trg_InsertCauHoi
- trg_UpdateCauHoi
- trg_DeleteCauHoi
- MERGE synchronization logic

---

## 💻 Giao diện hệ thống

(UI được chỉnh sửa từ template có sẵn)

  ### -Giao diện dữ liệu trực tuyến
  <img width="979" height="510" alt="image" src="https://github.com/user-attachments/assets/d3a924b2-baa9-4087-9ad6-65104a8b4623" />

  ### -Giao diện dữ liệu tạo sinh
  <img width="865" height="406" alt="image" src="https://github.com/user-attachments/assets/aab25abd-155e-4152-bcd9-969212c011ce" />

  ### -Giao diện dữ liệu thủ công
  <img width="865" height="420" alt="image" src="https://github.com/user-attachments/assets/dc6236de-5f95-495a-833c-f8b25773ea2f" />

---

## ⚙️ Công nghệ sử dụng

- SQL Server
- Trigger (AFTER INSERT / UPDATE / DELETE)
- MERGE statement
- Database design (ERD / schema design)
- C# WinForms (UI chỉnh sửa)

---

## 📊 Kết quả đạt được

- Thiết kế hệ thống quản lý dữ liệu nhiều database
- Tự động hóa đồng bộ dữ liệu bằng SQL Trigger
- Đảm bảo không trùng dữ liệu
- Xây dựng logic xử lý dữ liệu hoàn toàn bằng SQL
