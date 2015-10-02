/**
 *  Copyright 2014 Reverb Technologies, Inc.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

package com.github.kongchen.swagger.sample.wordnik.resource;

import com.github.kongchen.swagger.sample.wordnik.data.PetData;
import io.swagger.annotations.*;
import com.github.kongchen.swagger.sample.wordnik.model.Pet;
import io.swagger.annotations.ApiResponse;

import javax.ws.rs.core.Response;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.*;

/*api
* @Path("/pet")
* @Api(value = "/pet", description = "Operations about pets")
* @Produces({"application/json", "application/xml"})
*/
public class PetResource {
  static PetData petData = new PetData();
  static JavaRestResourceUtil ru = new JavaRestResourceUtil();

  /*api
  * @GET
  * @Path("/{petId}")
  * @ApiOperation(value = "Find pet by ID",
  *   notes = "Returns a pet when ID < 10.  ID > 10 or nonintegers will simulate API error conditions",
  *   response = "Pet.class"
  * )
  * @ApiResponses(value = { @ApiResponse(code = 400, message = "Invalid ID supplied"),
  *     @ApiResponse(code = 404, message = "Pet not found") })
  * @ApiImplicitParams(value = {
  *   @ApiImplicitParam(name = "petId", value = "ID of pet that needs to be fetched", allowableValues = "range[1,5]", required = true, dataType = "Long", paramType = "path")
  * })
  */
  public Response getPetById(Long petId)
      throws com.github.kongchen.swagger.sample.wordnik.exception.NotFoundException {
    Pet pet = petData.getPetbyId(petId);
    if (null != pet) {
      return Response.ok().entity(pet).build();
    } else {
      throw new com.github.kongchen.swagger.sample.wordnik.exception.NotFoundException(404, "Pet not found");
    }
  }

  /*api
  * @DELETE
  * @Path("/{petId}")
  * @ApiOperation(value = "Deletes a pet")
  * @ApiResponses(value = { @ApiResponse(code = 400, message = "Invalid pet value")})
  * @ApiImplicitParams(value = {
  *   @ApiImplicitParam(name = "apiKey", dataType = "String", paramType = "header"),
  *   @ApiImplicitParam(name = "petId", value = "Pet id to delete", required = true, dataType = "Long", paramType = "path")
  * })
  */
  public Response<LIST> deletePet(String apiKey, Long petId) {
    petData.deletePet(petId);
    return Response.ok().build();
  }

  /*api
  * @POST
  * @Consumes({"application/json", "application/xml"})
  * @ApiOperation(value = "Add a new pet to the store")
  * @ApiResponses(value = { @ApiResponse(code = 405, message = "Invalid input") })
  * @ApiImplicitParams(value = {
  *   @ApiImplicitParam(
  *      name = "pet", value = "Pet object that needs to be added to the store",
  *      required = true, paramType = "body"
  *   )
  * })
  */
  public Response addPet(Pet pet) {
    Pet updatedPet = petData.addPet(pet);
    return Response.ok().entity(updatedPet).build();
  }

  /*api
  * @PUT
  * @Consumes({"application/json", "application/xml"})
  * @ApiOperation(value = "Update an existing pet")
  * @ApiResponses(value = { @ApiResponse(code = 400, message = "Invalid ID supplied"),
  *     @ApiResponse(code = 404, message = "Pet not found"),
  *     @ApiResponse(code = 405, message = "Validation exception") })
  * @ApiImplicitParams(value = {
  *   @ApiImplicitParam(name = "pet", value = "Pet object that needs to be added to the store", required = true, dataType = "Pet", paramType = "body")
  * })
  */
  public Response updatePet(Pet pet) {
    Pet updatedPet = petData.addPet(pet);
    return Response.ok().entity(updatedPet).build();
  }

  /*api
  * @GET
  * @Path("/findByStatus")
  * @ApiOperation(value = "Finds Pets by status",
  *   notes = "Multiple status values can be provided with comma seperated strings",
  *   response = "Pet.class",
  *   responseContainer = "List")
  * @ApiResponses(value = { @ApiResponse(code = 400, message = "Invalid status value") })
  * @ApiImplicitParams(value = {
  *   @ApiImplicitParam(
  *      name = "status", value = "Status values that need to be considered for filter",
  *      required = true, defaultValue = "available", dataType = "String",
  *      allowableValues = "available,pending,sold", allowMultiple = true, paramType = "query"
  *   )
  * })
  */
  public Response findPetsByStatus(String status) {
    return Response.ok(petData.findPetByStatus(status)).build();
  }

  /*api
  * @GET
  * @Path("/findByTags")
  * @ApiOperation(value = "Finds Pets by tags",
  *   notes = "Muliple tags can be provided with comma seperated strings. Use tag1, tag2, tag3 for testing.",
  *   response = "Pet.class",
  *   responseContainer = "List")
  * @ApiResponses(value = { @ApiResponse(code = 400, message = "Invalid tag value") })
  * @ApiImplicitParams(value = {
  *   @ApiImplicitParam(
  *      name = "tags", value = "Tags to filter by",
  *      required = true, dataType = "String", allowMultiple = true, paramType = "query"
  *   )
  * })
  */
  @Deprecated
  public Response findPetsByTags(String tags) {
    return Response.ok(petData.findPetByTags(tags)).build();
  }

  /*api
  * @POST
  * @Path("/{petId}")
  * @Consumes({MediaType.APPLICATION_FORM_URLENCODED})
  * @ApiOperation(value = "Updates a pet in the store with form data",
  *   consumes = "MediaType.APPLICATION_FORM_URLENCODED")
  * @ApiResponses(value = {
  *   @ApiResponse(code = 405, message = "Invalid input")})
  * @ApiImplicitParams(value = {
  *   @ApiImplicitParam(
  *      name = "petId", value = "ID of pet that needs to be updated",
  *      required = true, dataType = "String", paramType = "path"
  *   ),
  *   @ApiImplicitParam(
  *      name = "name", value = "Updated name of the pet",
  *      required = false, dataType = "String", paramType = "form"
  *   ),
  *   @ApiImplicitParam(
  *      name = "status", value = "Updated status of the pet",
  *      required = false, dataType = "String", paramType = "formData"
  *   )
  * })
  */
  public Response updatePetWithForm (String petId, String name, String status) {
    System.out.println(name);
    System.out.println(status);
    return Response.ok().entity(new com.github.kongchen.swagger.sample.wordnik.model.ApiResponse(200, "SUCCESS")).build();
  }
}
