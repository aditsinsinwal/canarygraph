package com.canarygraph.domain.common;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.regex.Pattern;

public record ContentHash(String sha256) {

    private static final Pattern SHA_256 = Pattern.compile("[0-9a-f]{64}");

    public ContentHash {
        sha256 = DomainValidation.requireNonBlank(sha256, "sha256").toLowerCase();
        if (!SHA_256.matcher(sha256).matches()) {
            throw new IllegalArgumentException("sha256 must be 64 hexadecimal characters");
        }
    }

    public static ContentHash from(byte[] content) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(content.clone());
            return new ContentHash(HexFormat.of().formatHex(digest));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("JVM does not provide SHA-256", exception);
        }
    }

    @Override
    public String toString() {
        return sha256;
    }
}

