# StockFlow ERP Lite — Lisans Sistemi

## Klasör yapısı ve dağıtım kuralı

```
StockFlow_App/                 <- MÜŞTERİYE dağıtılır (PyInstaller ile paketlenir)
    main.py
    gui.py
    license.py                 <- içinde SADECE genel anahtar (public key) var
    database.py
    models.py

Gelistirici_Araclari_GIZLI/    <- SADECE SİZDE kalır, ASLA müşteriye gitmez
    generator.py                <- lisans üretme aracı (private key gerektirir)
    private_key.pem              <- GİZLİ özel anahtar (şifreli, parolalı)
    public_key.pem                <- license.py içine zaten gömülü, referans amaçlı
    ornek_musteri_license.dat     <- test için üretilmiş örnek lisans dosyası
```

**Kritik kural:** `Gelistirici_Araclari_GIZLI/` klasörü PyInstaller derlemesine,
git reposunun herkese açık kısmına veya müşteriye giden hiçbir pakete
KESİNLİKLE dahil edilmemelidir.

## Uçtan uca akış

1. **Bir kere:** `python generator.py init-keys` ile RSA-4096 anahtar çifti
   üretilir (bu depoda demo amaçlı zaten üretilmiş durumda — production'a
   geçmeden önce KENDİ anahtarınızı üretip `license.py` içindeki
   `PUBLIC_KEY_PEM` sabitini güncelleyin).
2. Müşteri programı ilk açtığında lisans bulunamadığı için `LicenseDialog`
   açılır, Machine ID'sini gösterir.
3. Müşteri bu Machine ID'yi size iletir (e-posta, form, vb.).
4. Siz: `python generator.py create --machine-id "..." --customer "..." --days 365`
   komutuyla imzalı `license.dat` üretip müşteriye gönderirsiniz.
5. Müşteri "Lisans Dosyası Seç" butonuyla dosyayı seçer; `license.py`
   imzayı genel anahtarla doğrular, Machine ID ve ürün adını kontrol eder,
   dosyayı yerel veri klasörüne kopyalar. Bir sonraki açılışta tekrar
   sorulmaz.

## Neden bu tasarım güvenli?

- **Asimetrik imza (RSA-PSS + SHA-256, 4096 bit):** Uygulama sadece genel
  anahtarı içerir; genel anahtarla *doğrulama* yapılabilir ama *imza
  üretilemez*. Yani tersine mühendislik ile `license.py`'nin tamamı okunsa
  bile, saldırgan geçerli bir `license.dat` **üretemez** — bunun için özel
  anahtar (sizde, şifreli, hiç dağıtılmayan) gerekir. Eski sistemde
  (`generate_license()` istemcide) bu fonksiyonun kendisi "şifreyi" ifşa
  ediyordu; RSA bu sınıfın açığını kökten kapatır.
- **Kanonik JSON serileştirme** (`sort_keys=True`, sabit ayraçlar):
  imzalanan ve doğrulanan bayt dizisinin her iki tarafta birebir aynı
  olmasını garanti eder; aksi halde imza rastgele "bozuk" görünebilirdi.
- **Machine ID bağlama:** Lisans dosyası belirli bir makineye kilitlenir
  (birden fazla donanım kaynağının SHA-256 özeti). Dosya kopyalanıp başka
  bir bilgisayara taşınsa dahi `machine_id` uyuşmadığı için reddedilir.
- **Süre kontrolü isteğe bağlı:** `expires` alanı `None` ise süresiz,
  doluysa yerel saatle karşılaştırılır (offline çalışan bir masaüstü
  uygulaması için saat sunucusuna bağımlılık tercih edilmedi — bu, kullanıcı
  sistem saatini geri alırsa süre kontrolünün atlatılabileceği anlamına
  gelir; bu, kabul edilen bir ödünleşimdir).
- **Tek imza, tek anahtar, tek gerçek kaynak:** `_canonical_payload_bytes()`
  fonksiyonu hem `license.py` hem `generator.py` içinde birebir aynıdır;
  bu tutarlılık imza doğrulamasının güvenilirliğinin temelidir.

## Dürüst sınır: hiçbir istemci tarafı koruma kırılamaz değildir

Bu tasarım, **lisans dosyasının sahtesini üretmeyi** (özel anahtar olmadan)
hesaplama açısından pratikte imkânsız hale getirir — bu, ticari bir ürün
için asıl önemli olan şeydir. Ancak yerel olarak çalışan herhangi bir Python
uygulamasında, yeterince motive bir saldırgan `is_license_valid()`
fonksiyonunun her zaman `True` döndürmesi için ikili dosyayı (derlenmiş
`.exe`) doğrudan yamalayabilir (patch). Bu sınıf saldırılara karşı ek
sertleştirme (100% çözüm değil, sadece maliyeti artırır):

- PyInstaller çıktısını bir obfuscator (örn. PyArmor) ile paketleyin.
- Kritik kontrolleri tek bir yerde değil, birkaç farklı noktada
  (ör. periyodik olarak arka planda) tekrar tekrar çağırın.
- Kod imzalama (code signing) sertifikası kullanarak `.exe`'nin
  değiştirilip değiştirilmediğini işletim sistemi seviyesinde
  tespit edilebilir hale getirin.
- Çok kritik ürünlerde bir "phone home" (çevrimiçi periyodik doğrulama)
  katmanı eklemeyi değerlendirin — bu depoda İSTENMEDİĞİ için dahil
  edilmedi, ancak offline bir masaüstü aracı için en güçlü ek katman
  budur.
