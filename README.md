# To-Do List Web Uygulaması - Bulut Bilişim Final Projesi

Öğrenci Adı: Esma Derya Uğuz  
Ders: Bulut Bilişim  
Teslim Tarihi: 3 Haziran 2026  

## 1. Proje Özeti

Bu proje, kullanıcıların yapılacaklar listesi oluşturmasını sağlayan bir web uygulamasını kapsamaktadır. Uygulama, Docker ile container hale getirilmiş ve Google Kubernetes Engine (GKE) üzerinde çalışacak şekilde yapılandırılmıştır. Kullanıcılar sisteme kayıt olup giriş yapabilmekte, todo ekleyebilmekte, silebilmekte, düzenleyebilmekte ve tamamlayabilmektedir. Ayrıca aktif ve tamamlanmış todoları filtreleyebilmekte, profil bilgilerini güncelleyebilmektedir.

Proje kapsamında aşağıdaki Kubernetes özellikleri kullanılmıştır:
- Deployment ile 3 replica çalıştırma ve RollingUpdate stratejisi
- LoadBalancer tipinde Service ile dış dünyaya açılma
- StatefulSet ile MySQL veritabanı yönetimi
- Persistent Volume Claim (PVC) ile 2GB kalıcı depolama
- NetworkPolicy ile güvenli erişim kontrolü
- Secret ile hassas verilerin güvenli saklanması
- Manual Scaling (ölçekleme) işlemleri
- Rolling update ve rollback mekanizmaları
- Cloud Build ile CI/CD pipeline

---

## 2. Teknoloji Stack

| Bileşen        | Teknoloji                  | Açıklama |
|----------------|----------------------------|----------|
| Backend        | Flask (Python)             | Web framework, kullanıcı yönetimi ve CRUD işlemleri |
| WSGI Sunucusu  | Gunicorn                   | Production ortamında verimli çalışma |
| Database       | MySQL 8.0                  | Veri saklama (users ve todos tabloları) |
| DB Driver      | PyMySQL                    | Python-MySQL bağlantısı |
| Container      | Docker                     | Uygulamanın containerization işlemi |
| Orchestration  | Kubernetes (GKE)           | Container yönetimi ve scaling |
| CI/CD          | Google Cloud Build         | Otomatik build ve deploy pipeline |
| Image Storage  | Google Container Registry  | Docker imajlarının saklanması |
| Load Balancing | Google Cloud Load Balancer | Dış trafiği uygulamaya yönlendirme |

---

## 3. Uygulama Mimarisi

Uygulama üç ana katmandan oluşmaktadır:

### 3.1 Sunum Katmanı (Presentation Layer)
HTML, CSS ve Jinja2 template yapısı ile oluşturulan kullanıcı arayüzüdür. Kullanıcıdan kayıt ve giriş bilgilerini alır, todo listesini gösterir ve profil yönetimi sağlar.

### 3.2 İş Katmanı (Business Layer)
Flask framework ile yazılmış backend uygulamasıdır. Kullanıcı oturumlarını yönetir, todo işlemleri için CRUD operasyonlarını gerçekleştirir ve REST API endpoint'lerini sağlar.

### 3.3 Veri Katmanı (Data Layer)
MySQL veritabanından oluşur. `users` tablosu id, email, username, password ve created_at alanlarını; `todos` tablosu ise id, user_id, title, description, completed, created_at ve updated_at alanlarını barındırır. StatefulSet ve PVC ile kalıcı depolama sağlanmıştır.

---

## 4. Sistem Mimarisi

### 4.1 Teknoloji Bileşenleri
- Flask: Port 8080'de çalışan web framework, Gunicorn WSGI sunucusu ile hizmet verir.
- MySQL: Port 3306'da çalışan veritabanı, todo ve kullanıcı verilerini saklar.
- Docker: Uygulamayı container haline getirir.
- GKE: Kubernetes orchestration sağlar (cluster: todo-cluster, zone: us-central1-a).
- Cloud Build: CI/CD pipeline (main branch trigger, cloudbuild.yaml config).

### 4.2 Google Cloud Servisleri
- Google Container Registry: Docker imajlarının saklandığı repo (gcr.io/todo-app-proje/todo-app).
- Load Balancing: External IP 34.60.50.177 üzerinden 80 portunu 8080'e yönlendirir.

### 4.3 Sistem Akışı
1. Geliştirici kodu GitHub'a push eder.
2. Cloud Build tetiklenir ve Docker imajı oluşturur.
3. İmaj Google Container Registry'ye push edilir.
4. GKE cluster imajı çeker ve rolling update yapar.
5. Load Balancer trafiği uygulamaya yönlendirir.
6. Kullanıcılar http://34.60.50.177 adresinden uygulamaya erişir.

---

## 5. Kubernetes Mimarisi

### 5.1 GKE Control Plane (Google tarafından yönetilir)
- API Server: Tüm API isteklerini karşılar.
- Scheduler: Pod'ları node'lara yerleştirir.
- Controller Manager: Deployment ve ReplicaSet'leri yönetir.
- etcd: Cluster veri deposu.

### 5.2 Worker Node'lar
- Sayı: 2 node
- Tip: e2-medium
- Zone: us-central1-a

### 5.3 Namespace
Tüm kaynaklar `todo-app` namespace'i altında toplanmıştır.

### 5.4 Deployment (todo-app)
- **replicas:** 3
- **strategy:** RollingUpdate
- **rollingUpdate.maxSurge:** 1
- **rollingUpdate.maxUnavailable:** 0
- **resources.requests:** CPU 100m, Memory 128Mi
- **resources.limits:** CPU 500m, Memory 256Mi

### 5.5 Service
- todo-app-service (LoadBalancer): External IP 34.60.50.177, Port 80 → 8080
- todo-db-service (ClusterIP): Port 3306

### 5.6 StatefulSet ve PVC
- StatefulSet: todo-db-stateful (1 replica, MySQL 8.0, pod adı: todo-db-stateful-0)
- PVC: db-storage, 2Gi, ReadWriteOnce, mount path: /var/lib/mysql

### 5.7 NetworkPolicy
- todo-network-policy: Sadece app=todo-app pod'larının MySQL'e (port 3306) erişmesine izin verir.

### 5.8 Secret
- todo-db-secret: MYSQL_ROOT_PASSWORD (todo123) ve MYSQL_DATABASE (tododb)

---

## 6. CI/CD Pipeline Akışı

### 6.1 Geliştirici Akışı
1. Kod yaz (app.py'de değişiklik)
2. git add .
3. git commit -m "v2.0"
4. git push origin main

### 6.2 GitHub Repository
- **URL:** https://github.com/deryauguz/to-do-app
- main branch'e push algılanır → Webhook tetiklenir → Cloud Build Trigger devreye girer

### 6.3 Cloud Build Pipeline (5 Adım)
1. Docker Build: `docker build -t gcr.io/todo-app-proje/todo-app:$COMMIT_SHA .` (latest tag de eklenir)
2. Docker Push: `docker push gcr.io/todo-app-proje/todo-app:$COMMIT_SHA`
3. GKE Bağlantı: `gcloud container clusters get-credentials todo-cluster --zone=us-central1-a`
4. Rolling Update: `kubectl set image deployment/todo-app todo-app=gcr.io/todo-app-proje/todo-app:$COMMIT_SHA -n todo-app`
5. Rollout Status: `kubectl rollout status deployment/todo-app -n todo-app --timeout=5m`

### 6.4 Sonuç
Yeni versiyon uygulama kesintisi olmadan yayına alınır ve kullanıcılar http://34.60.50.177 adresinden erişebilir.

---

## 7. Rolling Update, Rollback ve Ölçekleme

### 7.1 Rolling Update (Kesintisiz Güncelleme)

```bash
kubectl set image deployment/todo-app todo-app=gcr.io/todo-app-proje/todo-app:v2 -n todo-app
kubectl rollout status deployment/todo-app -n todo-app
```

### 7.2 Rollback (Geri Alma)

```bash
kubectl rollout undo deployment/todo-app -n todo-app
kubectl rollout history deployment/todo-app -n todo-app
kubectl rollout history deployment/todo-app --revision=1 -n todo-app
```

### 7.3 Manuel Ölçekleme (Scaling)

```bash
kubectl scale deployment todo-app --replicas=5 -n todo-app
kubectl get pods -n todo-app
kubectl scale deployment todo-app --replicas=3 -n todo-app
```

---

## 8. Kullanılan Komutlar

```bash
# Pod listesi
kubectl get pods -n todo-app

# Service listesi
kubectl get services -n todo-app

# PVC listesi
kubectl get pvc -n todo-app

# NetworkPolicy listesi
kubectl get networkpolicy -n todo-app

# Cloud Build geçmişi
gcloud builds list --limit=3

# Belirli bir build'in logları
gcloud builds log BUILD_ID

# Cluster'a bağlanma
gcloud container clusters get-credentials todo-cluster --zone=us-central1-a

# Node listesi
kubectl get nodes
```

---

## 9. Proje Dosya Yapısı

```
to-do-app/
├── app/
│   ├── app.py                  # Flask uygulama kodu
│   └── requirements.txt        # Python bağımlılıkları
├── templates/
│   ├── landing.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── profile.html
├── static/
│   └── style.css
├── k8s/
│   ├── namespace.yaml
│   ├── secret.yaml
│   ├── database.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── networkpolicy.yaml
├── Dockerfile
├── cloudbuild.yaml
└── README.md
```

---


**GitHub Repository:** https://github.com/deryauguz/to-do-app  
**Uygulama Adresi:** http://34.60.50.177


