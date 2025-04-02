package em.embedded.reservationsapi;

import java.util.List;
import java.util.Map;

import org.evomaster.client.java.controller.EmbeddedSutController;
import org.evomaster.client.java.controller.api.dto.AuthenticationDto;
import org.evomaster.client.java.controller.api.dto.SutInfoDto;
import org.evomaster.client.java.controller.internal.db.DbSpecification;
import org.evomaster.client.java.controller.problem.ProblemInfo;
import org.evomaster.client.java.controller.problem.RestProblem;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.testcontainers.containers.GenericContainer;

import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;

import sk.cyrilgavala.reservationsApi.ReservationsApi;


/**
 * Class used to start/stop the SUT. This will be controller by the EvoMaster process
 */
public class Run extends EmbeddedSutController {

    private int port;

    public static void main(String[] args) {

        int port = 40100;
        if (args.length > 0) {
            port = Integer.parseInt(args[0]);
        }

        Run controller = new Run(port);
        controller.port = port;
        controller.startSut();
    }


    private ConfigurableApplicationContext ctx;

    private static final int MONGODB_PORT = 27017;

    //https://www.mongodb.com/docs/drivers/java/sync/current/compatibility/
    private static final String MONGODB_VERSION = "4.4";

    private static final String MONGODB_DATABASE_NAME = "Reservations";

    private static final GenericContainer mongodbContainer = new GenericContainer("mongo:" + MONGODB_VERSION)
            .withExposedPorts(MONGODB_PORT);

    private String mongoDbUrl;

    private MongoClient mongoClient;

    public Run() {
        this(0);
    }

    public Run(int port) {
        setControllerPort(port);
    }


    @Override
    public String startSut() {

        mongodbContainer.start();
        mongoDbUrl = "mongodb://" + mongodbContainer.getContainerIpAddress() + ":" + mongodbContainer.getMappedPort(MONGODB_PORT) + "/" + MONGODB_DATABASE_NAME;
        mongoClient = MongoClients.create(mongoDbUrl);



        ctx = SpringApplication.run(ReservationsApi.class,
                new String[]{"--server.port="+this.port,
                        "--databaseUrl="+mongoDbUrl,
                        "--spring.data.mongodb.uri="+mongoDbUrl,
                        "--spring.cache.type=NONE"
                });

        return "http://localhost:" + getSutPort();
    }

    protected int getSutPort() {
        return (Integer) ((Map) ctx.getEnvironment()
                .getPropertySources().get("server.ports").getSource())
                .get("local.server.port");
    }


    @Override
    public boolean isSutRunning() {
        return ctx != null && ctx.isRunning();
    }

    @Override
    public void stopSut() {
        ctx.stop();
        ctx.close();

        mongodbContainer.stop();
    }

    @Override
    public String getPackagePrefixesToCover() {
        return "sk.cyrilgavala.reservationsApi.";
    }

    @Override
    public void resetStateOfSUT() {
        mongoClient.getDatabase(MONGODB_DATABASE_NAME).drop();
    }

    @Override
    public List<DbSpecification> getDbSpecifications() {
        return null;
    }


    @Override
    public List<AuthenticationDto> getInfoForAuthentication() {
        //TODO might need to setup JWT headers here
        return null;
    }




    @Override
    public ProblemInfo getProblemInfo() {
        return new RestProblem(
                "http://localhost:" + getSutPort() + "/v3/api-docs",
                null
        );
    }

    @Override
    public SutInfoDto.OutputFormat getPreferredOutputFormat() {
        return SutInfoDto.OutputFormat.JAVA_JUNIT_4;
    }


}
