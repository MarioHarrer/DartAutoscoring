package com.example.resource;

import com.example.model.DartScorePayload;
import com.example.model.ThrowResult;
import com.example.model.Massages;
import com.example.service.DartService;
import com.example.websocket.DartboardWebSocket;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.UUID;

@Path("/api/dart")
public class DartApiResource {

    @Inject
    DartService dartService;

    @Inject
    DartboardWebSocket webSocket;

    @POST
    @Path("/score")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response receiveScoreFromPython(DartScorePayload payload) {

        if (dartService.getMatch() != null && !dartService.getMatch().getGameState().isGameover()) {

            // NEU: Wenn Python meldet, dass nur eine Kamera umgeschaltet wurde -> "Zurückspulen"
            if (payload.isCorrection) {
                System.out.println("🔄 Korrektur empfangen! Mache letzten Wurf rückgängig...");
                UUID tempPlayerId = dartService.getMatch().getGameState().getCurrentplayerId();
                dartService.deleteLastThrow();
            }

            UUID currentPlayerId = dartService.getMatch().getGameState().getCurrentplayerId();
            ThrowResult throwResult = new ThrowResult(payload.score, payload.isDouble, payload.isTriple);

            Massages validationResult = dartService.messagethrows(currentPlayerId, throwResult);

            if (validationResult.isValid()) {
                dartService.processThrow(currentPlayerId, throwResult);
                String alertTitle = payload.isCorrection ? "Wurf korrigiert!" : "Wurf erkannt!";
                String jsonMessage = String.format(
                        "{\"type\":\"throwRegistered\", \"showAlert\":true, \"alertTitle\":\"%s\", \"alertText\":\"%s\", \"alertIcon\":\"success\"}",
                        alertTitle, payload.score + " Punkte"
                );
                webSocket.broadcast(jsonMessage);

            } else {
                ThrowResult bustThrow = new ThrowResult(0, false, false);
                dartService.processThrow(currentPlayerId, bustThrow);

                String jsonMessage = String.format(
                        "{\"type\":\"throwRegistered\", \"showAlert\":true, \"alertTitle\":\"%s\", \"alertText\":\"%s\", \"alertIcon\":\"error\"}",
                        validationResult.getTitle(), validationResult.getText()
                );
                webSocket.broadcast(jsonMessage);
            }
        }
        return Response.ok().build();
    }
}