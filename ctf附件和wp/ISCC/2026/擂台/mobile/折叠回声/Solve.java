import java.util.zip.ZipFile;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.security.MessageDigest;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public class Solve {

    static byte[] sha256(byte[] data) throws Exception {
        return MessageDigest.getInstance("SHA-256").digest(data);
    }

    static byte[] concat(byte[]... arrays) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        for (byte[] a : arrays) baos.write(a);
        return baos.toByteArray();
    }

    static byte[] xorStream(byte[] data, byte[] key) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        int i = 0, counter = 0;
        while (i < data.length) {
            byte[] sha = sha256(concat(key,
                new byte[]{(byte)counter, (byte)(counter>>8), (byte)(counter>>16), (byte)(counter>>24)}));
            for (int j = 0; j < sha.length && i < data.length; j++) {
                baos.write(data[i] ^ sha[j]);
                i++;
            }
            counter++;
        }
        return baos.toByteArray();
    }

    static byte[] runVm(byte[] bcode, byte[] rk, byte[] dd, byte[] cd, byte[] snap, int outLen) throws Exception {
        int[] regs = new int[8];
        byte[] seed = sha256(concat("vm-seed".getBytes("UTF-8"), rk, dd, cd, snap));
        for (int i2 = 0; i2 < 8; i2++) {
            int i3 = i2 * 4;
            int val = ((seed[i3+3] & 0xFF) << 24) | ((seed[i3] & 0xFF) | ((seed[i3+1] & 0xFF) << 8) | ((seed[i3+2] & 0xFF) << 16));
            regs[i2] = val ^ (-1640531527 * i2);
        }

        System.out.print("Initial regs: ");
        for (int r : regs) System.out.printf("%08x ", r);
        System.out.println();

        int ip = 0;
        while (ip + 3 < bcode.length) {
            int op = bcode[ip] & 0xFF;
            int rx = bcode[ip+1] & 7;
            int ry = bcode[ip+2] & 7;
            int rz = bcode[ip+3] & 7;
            int i10 = ip / 4;

            int i11 = ((dd[(ip/2) % dd.length] & 0xFF) ^
                       (rk[i10 % rk.length] & 0xFF) ^
                       (cd[(ip/3) % cd.length] & 0xFF) ^
                       (snap[i10 % snap.length] & 0xFF));

            switch (op & 7) {
                case 0: regs[rx] = Integer.rotateLeft((regs[ry] + i11) + ip, (rz + i11) & 31) ^ regs[rx]; break;
                case 1: regs[rx] = Integer.rotateLeft(regs[rx] + regs[ry] + (i11 << 1) + rz, (ry + rz + ip) & 31); break;
                case 2: regs[rx] = regs[rx] ^ ((Integer.reverseBytes(regs[rz]) ^ regs[ry]) + i11); break;
                case 3: int t = regs[rx]; regs[rx] = regs[ry] + i11; regs[ry] = Integer.rotateRight(regs[rz] + ip, i11 & 31) ^ t; break;
                case 4: regs[rx] = regs[rx] + Integer.rotateRight((i11 ^ regs[ry]) ^ ip, (rz + rx + 1) & 31); break;
                case 5: regs[rx] = Integer.rotateLeft((regs[ry] + regs[rz]) + i11, ((ip + rx) + ry) & 31) ^ regs[rx]; break;
                case 6: regs[rx] = (i11 ^ (regs[rx] ^ regs[ry])) + Integer.reverse(regs[rz] + ip); break;
                default: regs[rx] = regs[rx] + (i11 ^ (regs[rz] ^ regs[ry])) + ip; break;
            }
            ip += 4;
        }

        System.out.print("Final regs: ");
        for (int r : regs) System.out.printf("%08x ", r);
        System.out.println();

        byte[] out = new byte[outLen];
        for (int i = 0; i < outLen; i++) {
            int val = (regs[i & 7] ^ Integer.rotateLeft(regs[(i+3) & 7], i & 31)) ^
                      (rk[i % rk.length] & 0xFF) ^
                      (dd[i % dd.length] & 0xFF) ^
                      (cd[i % cd.length] & 0xFF) ^
                      (snap[i % snap.length] & 0xFF);
            out[i] = (byte)val;
        }
        return out;
    }

    public static void main(String[] args) throws Exception {
        // Read ECH0 chunk from webp
        java.io.File f = new java.io.File("resources/assets/sleep_loop.webp");
        byte[] webpData = java.nio.file.Files.readAllBytes(f.toPath());

        byte[] echoData = null;
        int pos = 12;
        while (pos + 8 <= webpData.length) {
            String id = new String(webpData, pos, 4, "US-ASCII");
            int sz = (webpData[pos+7] << 24) | (webpData[pos+4] & 0xFF) | ((webpData[pos+5] & 0xFF) << 8) | ((webpData[pos+6] & 0xFF) << 16);
            if ("ECH0".equals(id)) {
                echoData = java.util.Arrays.copyOfRange(webpData, pos+8, pos+8+sz);
                break;
            }
            pos += 8 + sz + (sz & 1);
        }
        System.out.println("ECH0 size: " + echoData.length);

        // Environment values
        int[] echoFoldPulse = new int[32];
        for (int i = 0; i < 32; i++) echoFoldPulse[i] = 0x7f010000 + i;

        byte[] rk = new byte[24];
        for (int i = 0; i < 24; i++) {
            int i2 = echoFoldPulse[i % 32];
            int diff = (echoFoldPulse[(i+1) % 32] - i2) & 0xFF;
            rk[i] = (byte)((diff ^ ((i2 & 0x7F) << 1)) ^ (i * 13));
        }
        System.out.print("resourceKey: "); printHex(rk);

        // Read APK to get dex and cert
        ZipFile zf = new ZipFile("EchoFold.apk");
        byte[] dexData = readAll(zf.getInputStream(zf.getEntry("classes.dex")));
        byte[] dd = sha256(dexData);
        System.out.print("dexDigest: "); printHex(dd);
        zf.close();

        // Extract certificate from the RSA file
        byte[] rsaData = readAll(new java.util.zip.ZipFile("EchoFold.apk").getInputStream(
            new java.util.zip.ZipFile("EchoFold.apk").getEntry("META-INF/ECHOFOLD.RSA")));
        // Extract cert from PKCS7 SignedData
        java.security.cert.CertificateFactory cf = java.security.cert.CertificateFactory.getInstance("X.509");
        java.util.Collection<? extends java.security.cert.Certificate> chain = cf.generateCertificates(
            new java.io.ByteArrayInputStream(rsaData));
        byte[] certBytes = chain.iterator().next().getEncoded();
        byte[] cd = sha256(certBytes);
        System.out.print("certDigest: "); printHex(cd);
        System.out.println("cert size: " + certBytes.length);

        byte[] snap = new byte[]{17, 35, 122, 66, 81, 102};

        // Decrypt ECH0 chunk
        byte[] xorKey = sha256(concat("fold-echo".getBytes("UTF-8"), rk, dd, cd, snap));
        System.out.print("xorKey: "); printHex(xorKey);

        byte[] decrypted = xorStream(echoData, xorKey);
        System.out.print("Decrypted: "); printHex(decrypted);

        int bcodeLen = (decrypted[5] & 0xFF) << 8 | (decrypted[6] & 0xFF);
        int outLen = (decrypted[7] & 0xFF) << 8 | (decrypted[8] & 0xFF);
        System.out.println("bcodeLen=" + bcodeLen + " outLen=" + outLen);

        byte[] bcode = java.util.Arrays.copyOfRange(decrypted, 9, 9 + bcodeLen);
        byte[] encOutput = java.util.Arrays.copyOfRange(decrypted, 9 + bcodeLen, 9 + bcodeLen + outLen);
        System.out.print("encOutput: "); printHex(encOutput);

        // Run VM
        byte[] vmKey = runVm(bcode, rk, dd, cd, snap, outLen);
        System.out.print("vmKey: "); printHex(vmKey);

        // Decrypt flag
        byte[] flagContent = xorStream(encOutput, vmKey);
        System.out.print("Flag content: "); printHex(flagContent);
        System.out.print("Flag text: ");
        for (byte b : flagContent) System.out.print((char)(b & 0xFF));
        System.out.println();
        System.out.println("FLAG: ISCC{" + new String(flagContent, "UTF-8") + "}");
    }

    static byte[] readAll(InputStream is) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        while (true) {
            int r = is.read(buf);
            if (r < 0) { is.close(); return baos.toByteArray(); }
            baos.write(buf, 0, r);
        }
    }

    static void printHex(byte[] data) {
        for (byte b : data) System.out.printf("%02x", b & 0xFF);
        System.out.println();
    }
}
