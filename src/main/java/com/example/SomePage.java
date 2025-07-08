package com.example;

import io.quarkus.qute.Template;
import io.quarkus.qute.TemplateInstance;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

import static java.util.Objects.requireNonNull;

@Path("/spiel")
public class SomePage {

    private final Template page;
    private final Template match;


    public SomePage(Template page, Template match) {
        this.page = requireNonNull(page, "page is required");
        this.match = match;
    }

    @GET
    @Produces(MediaType.TEXT_HTML)
    public TemplateInstance get(@QueryParam("name") String name) {
        return page.data("name", name).data("game", "lol");
    }

    @GET
    @Path("/match")
    @Produces(MediaType.TEXT_HTML)
    public TemplateInstance getGame1(@QueryParam("name") String name) {
        return match.data("game", "match");
    }

    @GET
    @Path("/around-the-clock")
    @Produces(MediaType.TEXT_HTML)
    public TemplateInstance getGame2(@QueryParam("name") String name) {
        return page.data("game", "around-the-clock");
    }

}
