package sk.cyrilgavala.reservationsApi.mapper;

import javax.annotation.processing.Generated;
import org.springframework.stereotype.Component;
import sk.cyrilgavala.reservationsApi.model.User;
import sk.cyrilgavala.reservationsApi.web.response.UserResponse;

@Generated(
    value = "org.mapstruct.ap.MappingProcessor",
    date = "2024-01-12T12:41:44+0800",
    comments = "version: 1.4.2.Final, compiler: Eclipse JDT (IDE) 3.37.0.v20240103-0614, environment: Java 17.0.9 (Eclipse Adoptium)"
)
@Component
public class UserMapperImpl implements UserMapper {

    @Override
    public UserResponse modelToResponse(User model) {
        if ( model == null ) {
            return null;
        }

        UserResponse userResponse = new UserResponse();

        userResponse.setEmail( model.getEmail() );
        userResponse.setId( model.getId() );
        userResponse.setPassword( model.getPassword() );
        userResponse.setRole( model.getRole() );
        userResponse.setUsername( model.getUsername() );

        return userResponse;
    }
}
