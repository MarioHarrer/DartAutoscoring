
package com.example;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.core.Response;
import java.net.URI;

@Path("/")
public class RootRedirectResource {

    @GET
    public Response redirectToDartboard() {
        return Response.status(Response.Status.FOUND)
                .location(URI.create("/dartboard"))
                .build();
    }
}
