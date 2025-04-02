package sk.cyrilgavala.reservationsApi.mapper;

import javax.annotation.processing.Generated;
import org.springframework.stereotype.Component;
import sk.cyrilgavala.reservationsApi.model.Reservation;
import sk.cyrilgavala.reservationsApi.web.request.CreateReservationRequest;
import sk.cyrilgavala.reservationsApi.web.request.UpdateReservationRequest;
import sk.cyrilgavala.reservationsApi.web.response.ReservationResponse;

@Generated(
    value = "org.mapstruct.ap.MappingProcessor",
    date = "2024-01-12T12:41:44+0800",
    comments = "version: 1.4.2.Final, compiler: Eclipse JDT (IDE) 3.37.0.v20240103-0614, environment: Java 17.0.9 (Eclipse Adoptium)"
)
@Component
public class ReservationMapperImpl implements ReservationMapper {

    @Override
    public Reservation createRequestToModel(CreateReservationRequest request) {
        if ( request == null ) {
            return null;
        }

        Reservation reservation = new Reservation();

        reservation.setCreatedAt( request.getCreatedAt() );
        reservation.setReservationFor( request.getReservationFor() );
        reservation.setReservationFrom( request.getReservationFrom() );
        reservation.setReservationTo( request.getReservationTo() );

        return reservation;
    }

    @Override
    public Reservation updateRequestToModel(Reservation model, UpdateReservationRequest request) {
        if ( request == null ) {
            return null;
        }

        model.setReservationFor( request.getReservationFor() );
        model.setReservationFrom( request.getReservationFrom() );
        model.setReservationTo( request.getReservationTo() );
        model.setUuid( request.getUuid() );

        return model;
    }

    @Override
    public ReservationResponse modelToResponse(Reservation model) {
        if ( model == null ) {
            return null;
        }

        ReservationResponse reservationResponse = new ReservationResponse();

        reservationResponse.setReservationFor( model.getReservationFor() );
        reservationResponse.setReservationFrom( model.getReservationFrom() );
        reservationResponse.setReservationTo( model.getReservationTo() );
        reservationResponse.setUuid( model.getUuid() );

        return reservationResponse;
    }
}
