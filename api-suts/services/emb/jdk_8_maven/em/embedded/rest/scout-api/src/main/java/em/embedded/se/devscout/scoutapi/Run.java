package em.embedded.se.devscout.scoutapi;

import org.evomaster.client.java.controller.AuthUtils;
import org.evomaster.client.java.controller.EmbeddedSutController;
import org.evomaster.client.java.controller.InstrumentedSutStarter;
import org.evomaster.client.java.controller.api.dto.database.schema.DatabaseType;
import org.evomaster.client.java.controller.db.DbCleaner;
import org.evomaster.client.java.controller.db.SqlScriptRunner;
import org.evomaster.client.java.controller.internal.db.DbSpecification;
import org.evomaster.client.java.controller.problem.ProblemInfo;
import org.evomaster.client.java.controller.problem.RestProblem;
import org.evomaster.client.java.controller.api.dto.AuthenticationDto;
import org.evomaster.client.java.controller.api.dto.HeaderDto;
import org.evomaster.client.java.controller.api.dto.SutInfoDto;
import se.devscout.scoutapi.ScoutAPIApplication;

import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.Arrays;
import java.util.List;

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


    private ScoutAPIApplication application;
    private Connection sqlConnection;
//    private final List<String> sqlCommands;

    private String INIT_DB_SCRIPT_PATH = "/init_db.sql";

    private List<DbSpecification> dbSpecification;


    public Run() {
        this(40100);
    }

    public Run(int port) {
        setControllerPort(port);
    }

    @Override
    public String startSut() {
        application = new ScoutAPIApplication();

        //Dirty hack for DW...
        System.setProperty("dw.server.connector.port", Integer.toString(this.port));

        try {
            application.run("server", "src/main/resources/scout_api_evomaster.yml");
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }

        try {
            Thread.sleep(3_000);
        } catch (InterruptedException e) {
        }

        while (!application.getJettyServer().isStarted()) {
            try {
                Thread.sleep(1_000);
            } catch (InterruptedException e) {
            }
        }

        sqlConnection = application.getConnection();

        /*
            ensure that the database is clean
         */
        DbCleaner.clearDatabase_H2(sqlConnection);

        dbSpecification = Arrays.asList(new DbSpecification(DatabaseType.H2,sqlConnection)
                .withInitSqlOnResourcePath(INIT_DB_SCRIPT_PATH));

        resetStateOfSUT();

        return "http://localhost:" + application.getJettyPort();
    }


    @Override
    public boolean isSutRunning() {
        if (application == null) {
            return false;
        }

        return application.getJettyServer().isRunning();
    }

    @Override
    public void stopSut() {
        if (application != null) {
            try {
                application.getJettyServer().stop();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        if (sqlConnection != null) {
            try {
                sqlConnection.close();
            } catch (SQLException e) {
                e.printStackTrace();
            }
        }
    }

    @Override
    public String getPackagePrefixesToCover() {
        return "se.devscout.";
    }

    @Override
    public void resetStateOfSUT() {

        deleteDir(new File("./target/temp"));

//        DbCleaner.clearDatabase_H2(sqlConnection);
//        SqlScriptRunner.runCommands(sqlConnection, sqlCommands);
    }


    @Override
    public List<AuthenticationDto> getInfoForAuthentication() {
        return Arrays.asList(
                AuthUtils.getForAuthorizationHeader("user", "ApiKey user"),
                AuthUtils.getForAuthorizationHeader("moderator", "ApiKey moderator"),
                AuthUtils.getForAuthorizationHeader("administrator", "ApiKey administrator")
        );
    }



    @Override
    public ProblemInfo getProblemInfo() {
        return new RestProblem(
                "http://localhost:" + application.getJettyPort() + "/api/swagger.json",
                null
        );
    }

    @Override
    public SutInfoDto.OutputFormat getPreferredOutputFormat() {
        return SutInfoDto.OutputFormat.JAVA_JUNIT_4;
    }


    private void deleteDir(File file) {
        File[] contents = file.listFiles();
        if (contents != null) {
            for (File f : contents) {
                deleteDir(f);
            }
        }
        file.delete();
    }

    @Override
    public List<DbSpecification> getDbSpecifications() {
        return dbSpecification;
    }
}
