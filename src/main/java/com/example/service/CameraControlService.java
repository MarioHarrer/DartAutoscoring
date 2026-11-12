package com.example.service;

import jakarta.enterprise.context.ApplicationScoped;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@ApplicationScoped
public class CameraControlService {

    private final HttpClient httpClient = HttpClient.newHttpClient();

    public void startPythonCameras() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create("http://localhost:5000/api/camera/start"))
                    .POST(HttpRequest.BodyPublishers.noBody())
                    .build();

            // Sendet asynchron, damit das Java-Backend nicht blockiert
            httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenAccept(res -> System.out.println("Kamerasignal an Python gesendet (Port 5000)"));
        } catch (Exception e) {
            System.out.println("Fehler: Python-Skript ist nicht unter Port 5000 erreichbar.");
        }
    }
}