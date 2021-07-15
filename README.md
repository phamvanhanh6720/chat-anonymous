# chat-anonymous 
Đây là một ứng dụng trò chuyện đơn giản, ẩn danh và được mã hóa hoàn toàn.

# About
Ứng dụng được xây dựng bằng cách sử dụng thư viện socket có trong Python. Các client kết nối với server và sau đó server sẽ cho phép họ gửi tin nhắn văn bản cho nhau.  
Những tin nhắn này được mã hóa bằng AES-256 để đảm bảo tính riêng tư và ẩn danh cho người dùng. Ngoài ra chúng tôi cũng không thu thập bất kỳ dữ liệu nào của người dùng.  
Về trao đổi khóa được thực hiện bằng phương pháp DiffieHellman và GUI được xây dựng bằng thư viện Eel.


# Cuộc trò chuyện

Mỗi client sẽ có private key của mình và chỉ được chia sẻ khóa này cho server. Server sẽ mã hóa và giải mã thông điệp bằng khóa tương ứng cho các client khác trong cuộc trò chuyện.


# Ẩn danh

Để bắt đầu sử dụng chat-anonymous, bạn không cần bất kỳ loại tài khoản nào. Mọi thứ ở đây đều ẩn danh, bạn chỉ cần quan tâm đến địa chỉ IP của mình.

# Requirements
Cài đặt một số thư viện sau:

* dataclasses_json
* pycryptodome
* pyDHE
* Eel

# Run

Lưu ý: bạn phải chạy server trước client. Nếu bạn muốn kích hoạt nhiều client(để debug), hãy truy cập client.py và bỏ nhận xét hàm dưới đây: 


```
eel.start('main.html', port=random.choice(range(8000, 8080)))
```

### 1st option:

```
python3 server.py -p <port number>
```
```
python3 client.py -s <server_ip> -p <server_port>
```

### 2nd option:

```
python3 server.py
```
```
python3 client.py
```


