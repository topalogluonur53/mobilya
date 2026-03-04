# Mutfak Dolabı Planlayıcı (Kitchen Cabinet Planner)

Bu proje, Django ve Vanilla JS kullanılarak geliştirilmiş bir "Mutfak Dolabı Planlayıcı" uygulamasıdır. Kullanıcılar düz (STRAIGHT) veya L tipi (L-Shape) mutfak duvarlarına beyaz eşyalar (buzdolabı, bulaşık makinesi, fırın, evye vb.) yerleştirebilir, kalan boşlukları otomatik olarak standart alt (BASE) ve üst (WALL) dolaplarla doldurarak 18mm MDF için kesim listesi alabilir.

## Teknoloji Yığıtı
- **Backend:** Python + Django + Django REST Framework + SQLite
- **Frontend:** Vanilla JS + CSS Variables + SVG çizim + HTML5 Dashboard
- **Algoritma:** Boşluklara göre Dinamik Programlama (DP) destekli modül optimizasyonu.

## Kurulum ve Çalıştırma

1. Python 3'ün sisteminizde kurulu olduğundan emin olun.
2. Proje dizininde bir sanal ortam oluşturun ve bağımlılıkları yükleyin:
   ```bash
   python -m venv venv
   
   # Windows için
   .\venv\Scripts\activate
   # macOS/Linux için
   # source venv/bin/activate
   
   pip install django djangorestframework django-cors-headers
   ```
3. Veritabanını oluşturun:
   ```bash
   python manage.py makemigrations planner
   python manage.py migrate
   ```
4. Geliştirme sunucusunu başlatın:
   ```bash
   python manage.py runserver
   ```
5. Tarayıcınızda açın:
   http://127.0.0.1:8000/

## API Kullanımı 

API uç noktalarına şu adreslerden ulaşılabilir:
- **`GET /api/projects/`**: Projeleri listele
- **`POST /api/segments/`**: Yeni segment parçası (A / B duvarları) oluştur
- **`POST /api/appliances/`**: Belirlenen segmente Appliance (Beyaz eşya) ekle
- **`POST /api/projects/{id}/generate/`**: Yerleşim motorunu (layout engine) devreye sokar, boşlukları Base ve Wall modülleri ile doldurur
- **`GET /api/projects/{id}/cutlist/`**: Üretilmiş yerleşimin MDF 18mm Kesim listesini JSON olarak döndürür
- **`GET /api/projects/{id}/cutlist_csv/`**: Kesim listesini CSV dosyası olarak indirir

Örnek cURL Komutu:
```bash
curl -X POST http://127.0.0.1:8000/api/projects/1/generate/
```

## İlk Çalıştırma Adımları ve UI Akışı
1. Arayüzde bir proje ismi ve türü (Düz veya L) belirleyerek "Proje Oluştur" butonuna basın.
2. Segment (duvar genişliği) ölçülerini girin (örn: 3000 mm).
3. Ekrana eklemek istediğiniz beyaz eşyaların tipini (örn: FRIDGE) ve başlangıç koordinatını (X mm) yazarak soldan doldurun.
4. Çakışma kurallarına dikkat ediniz (çakışma durumunda UI hata verecektir).
5. "Yerleşimi Üret" tuşuna bastığınızda motor çalışır; boşluklara 300, 400, 450, 500, 600, 800, 900 mm modülleri yerleşerek dolgu paneli minimize edilecek şekilde hesaplama yapılır.
6. Hem SVG önizlemesini hem de CSV kesim listesini eş zamanlı olarak kullanabilirsiniz.
