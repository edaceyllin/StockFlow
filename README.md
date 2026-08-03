# StockFlow 📦

Küçük işletmeler için geliştirilmiş masaüstü stok yönetim sistemi.

## 📌 Proje Hakkında

StockFlow; ürün takibi, stok yönetimi ve temel satış işlemlerini kolaylaştırmak amacıyla geliştirilmiş bir masaüstü uygulamasıdır.

Uygulama, küçük işletmelerin ürünlerini daha düzenli takip edebilmesi, stok durumlarını kontrol edebilmesi ve satış süreçlerini yönetebilmesi için tasarlanmıştır.

## ✨ Özellikler

- ✅ Ürün ekleme
- ✅ Ürün listeleme
- ✅ Ürün güncelleme
- ✅ Ürün silme
- ✅ Barkod ile ürün takibi
- ✅ Stok kontrolü
- ✅ Satış kayıtları
- ✅ Düşük stok takibi
- ✅ Excel aktarımı
- ✅ Lisans doğrulama sistemi

## 🛠 Kullanılan Teknolojiler

- Python
- PyQt6
- SQLite
- OpenPyXL
- Cryptography

## 📁 Proje Yapısı

```text
StockFlow_App
│
├── main.py              # Uygulama başlangıç noktası
├── gui.py               # Kullanıcı arayüzü
├── database.py          # Veritabanı işlemleri
├── models.py            # Veri modelleri
├── license.py           # Lisans kontrol sistemi
└── requirements.txt     # Gerekli paketler
```

## ⚙️ Kurulum

Projeyi klonladıktan sonra gerekli paketleri yükleyin:

```bash
pip install -r requirements.txt
```

Uygulamayı çalıştırmak için:

```bash
python main.py
```

## 🔒 Lisans Sistemi

StockFlow içerisinde lisans doğrulama altyapısı bulunmaktadır.

Geliştirici lisans araçları ve özel anahtar dosyaları güvenlik nedeniyle projeden ayrı tutulmaktadır.

##  Veritabanı

Uygulama SQLite veritabanı kullanmaktadır.

Kullanıcı verileri ve işletmeye özel stok kayıtları uygulama içerisinde oluşturulur.

##  Geliştirme Süreci

Bu proje küçük işletmeler için kullanılabilecek profesyonel bir stok yönetim sistemi geliştirme amacıyla oluşturulmuştur.

Geliştirme sürecinde masaüstü uygulama mimarisi, veritabanı yönetimi, kullanıcı arayüzü tasarımı ve lisanslama sistemi üzerine çalışılmıştır.

---

Developed with Python
