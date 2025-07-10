package com.example.resource;

import com.example.model.*;
import com.example.service.DartService;
import io.quarkus.qute.Template;
import io.quarkus.qute.TemplateInstance;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.net.URI;
import java.util.List;
import java.util.UUID;

@Path("/dartboard")
public class DartboardResource {

    @Inject
    Template dartboard;

    @Inject
    DartService dartService;

    @GET
    @Produces(MediaType.TEXT_HTML)
    public TemplateInstance get() {
        return dartboard
                .data("players", dartService.getPlayers())
                .data("match", dartService.getMatch())
                .data("playerMap", dartService.getPlayerMap());
    }

    @POST
    @Path("/player")
    @Consumes(MediaType.APPLICATION_FORM_URLENCODED)
    public Response addPlayer(@FormParam("name") String name) {
        dartService.addPlayer(name);
        return Response.seeOther(URI.create("/dartboard")).build();
    }

    @POST
    @Path(("/match/end"))
    public Response endMatch() {
        dartService.endMatch();
        return Response.seeOther(URI.create("/dartboard")).build();
    }

    @POST
    @Path("/match")
    @Consumes(MediaType.APPLICATION_FORM_URLENCODED)
    public Response startMatch(@FormParam("players") List<UUID> playerIds,
                               @FormParam("modeType") MatchModeType modeType,
                               @FormParam("startMode") StartMode startMode,
                               @FormParam("endMode") EndMode endMode) {
        if (playerIds.isEmpty() || playerIds.size() > 4) {
            throw new WebApplicationException("Bitte 1 bis 4 Spieler auswählen", 400);
        }


        MatchMode matchMode = new MatchMode(modeType, startMode, endMode);
        dartService.startNewMatch(playerIds, matchMode );
        return Response.seeOther(URI.create("/dartboard")).build();
    }


    @POST
    @Path("/throw")
    /*public Response throwDart(@FormParam("playerId") UUID playerId,
                               @FormParam("throw") int throwValue) {
        //dartService.getMatch().getScores().put(playerId, throwValue);*/
    public Response throwDart(@FormParam("throw") int throwValue) {
        try {
            Match match = dartService.getMatch();
            if (match == null) {
                throw new WebApplicationException("Kein Spiel gestartet", 400);
            }
            dartService.processThrow(match.getGameState().getCurrentplayerId(), throwValue);
            return Response.seeOther(URI.create("/dartboard")).build();
        }catch (IllegalArgumentException e){
            throw new WebApplicationException(e.getMessage(), 400);
        }

    }



}
