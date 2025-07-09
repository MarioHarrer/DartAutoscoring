package com.example;

import io.quarkus.qute.Template;
import io.quarkus.qute.TemplateInstance;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

import static java.util.Objects.requireNonNull;

@Path("/")
public class SomePage {

    private final Template page;
    private final Template match;
    private final Template around;

    public SomePage(Template match, Template page, Template around) {
        this.match = requireNonNull(match, "match is required");
        this.page = requireNonNull(page, "page is required");
        this.around = requireNonNull(around, "around is required");
    }

    @GET
    @Path("/match")
    @Produces(MediaType.TEXT_HTML)
    public TemplateInstance getMatch() {
        return match.data("mode", "match");
    }

    @GET
    @Path("/match/spiel")
    @Produces(MediaType.TEXT_HTML)
    public TemplateInstance getMatchGame() {
        return page.data("game", "match");
    }

    @GET
    @Path("/around-the-clock")
    @Produces(MediaType.TEXT_HTML)
    public TemplateInstance getAroundTheClock() {
        return around.data("mode", "around-the-clock");
    }

    @GET
    @Path("/around-the-clock/spiel")
    @Produces(MediaType.TEXT_HTML)
    public TemplateInstance getAroundTheClockGame() {
        return page.data("game", "around-the-clock");
    }
}

