from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Виконується один раз при підключенні користувача"""
        response = self.client.post("/api/auth/login/", json={
            "email": "mobtest@example.com",
            "password": "12345678" 
        })
        if response.status_code == 200:
            token = response.json()["access"]
            self.client.headers["Authorization"] = f"Bearer {token}"
        else:
            print(f"Помилка логіну: {response.status_code} - {response.text}")

    @task(3)  
    def get_plant_types(self):
        self.client.get("/api/plant-types/")

    @task(1)  
    def get_my_plants(self):
        self.client.get("/api/plants/")