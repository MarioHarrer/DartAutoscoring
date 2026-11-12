package com.example.resource;

import com.example.model.DartScorePayload;
import com.example.model.ThrowResult;
import com.example.service.DartService;
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

    @POST
    @Path("/score")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response receiveScoreFromPython(DartScorePayload payload) {
        if (dartService.getMatch() != null && !dartService.getMatch().getGameState().isGameover()) {
            UUID currentPlayerId = dartService.getMatch().getGameState().getCurrentplayerId();
            ThrowResult throwResult = new ThrowResult(payload.score, payload.isDouble, payload.isTriple);

            // Führt den Wurf aus, als hätte der Nutzer auf die Web-Scheibe geklickt
            dartService.processThrow(currentPlayerId, throwResult);
            System.out.println("Wurf registriert: " + payload.score);
        }
        return Response.ok().build();
    }
}