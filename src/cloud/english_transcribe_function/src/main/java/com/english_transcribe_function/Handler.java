package com.english_transcribe_function;

import com.amazonaws.auth.AWSStaticCredentialsProvider;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.GetObjectRequest;
import com.amazonaws.services.s3.model.S3Object;
import org.apache.commons.io.FileUtils;
import org.apache.log4j.Logger;
import org.reactivestreams.Publisher;
import org.reactivestreams.Subscriber;
import org.reactivestreams.Subscription;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.AwsCredentialsProvider;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.auth.signer.EventStreamAws4Signer;
import software.amazon.awssdk.core.SdkBytes;
import software.amazon.awssdk.core.client.config.SdkAdvancedClientOption;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.transcribestreaming.TranscribeStreamingAsyncClient;
import software.amazon.awssdk.services.transcribestreaming.model.*;

import java.io.*;
import java.net.URI;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicLong;

public class Handler {

    private static final Logger LOG = Logger.getLogger(Handler.class);
    private static final String endpoint = "https://transcribestreaming.us-east-1.amazonaws.com";

    public String lambdaHandler(S3ObjectInfo s3ObjectInfo, Context context) throws Exception {
        LOG.info("received: " + s3ObjectInfo.getBucketName() + " " + s3ObjectInfo.getObjectKey());

        TranscribeStreamingAsyncClient client = TranscribeStreamingAsyncClient.builder()
                .overrideConfiguration(
                        c -> c.putAdvancedOption(
                                SdkAdvancedClientOption.SIGNER,
                                EventStreamAws4Signer.create()))
                .credentialsProvider(getCredentials())
                .endpointOverride(new URI(endpoint))
                .region(Region.US_EAST_1)
                .build();

        OutputCollector collector = new OutputCollector();
        /**
         * Start real-time speech recognition. Transcribe streaming java client uses Reactive-streams interface.
         * For reference on Reactive-streams: https://github.com/reactive-streams/reactive-streams-jvm
         */
        CompletableFuture<Void> result = client.startStreamTranscription(
                /**
                 * Request parameters. Refer to API document for details.
                 */
                getRequest(44_100),
                    new AudioStreamPublisher(getStreamFromS3Object(s3ObjectInfo)),
                /**
                 * Subscriber of real-time transcript stream.
                 * Output will print to your computer's standard output.
                 */
                getResponseHandler(collector));

        /**
         * Synchronous wait for stream to close, and close client connection
         */
        result.get();
        String output = collector.getOutput();

        return output;
    }

    private static InputStream getStreamFromS3Object(S3ObjectInfo s3ObjectInfo) {
        AmazonS3 s3Client = AmazonS3ClientBuilder.standard()
                .withRegion(Regions.US_EAST_1)
                .withCredentials(new AWSStaticCredentialsProvider(new BasicAWSCredentials(System.getenv("OVERRIDE_AWS_ACCESS_KEY_ID"), System.getenv("OVERRIDE_AWS_SECRET_ACCESS_KEY"))))
                .build();
        S3Object fullObject = s3Client.getObject(new GetObjectRequest(s3ObjectInfo.getBucketName(), s3ObjectInfo.getObjectKey()));

        InputStream objectContent = fullObject.getObjectContent();

        try {
            File targetFile = File.createTempFile("talko-lingo", ".wav", new File("/tmp"));
            FileUtils.copyInputStreamToFile(objectContent, targetFile);
            return new FileInputStream(targetFile);
        } catch (FileNotFoundException e) {
            throw new RuntimeException(e);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private static StartStreamTranscriptionRequest getRequest(Integer mediaSampleRateHertz) {
        return StartStreamTranscriptionRequest.builder()
                .languageCode(LanguageCode.EN_US.toString())
                .mediaEncoding(MediaEncoding.PCM)
                .mediaSampleRateHertz(mediaSampleRateHertz)
                .build();
    }

    private static class OutputCollector {
        private String msg;

        public OutputCollector() {
        }

        public void collect(String msg) {
            this.msg = msg;
        }

        public String getOutput() {
            return this.msg;
        }
    }

    private static StartStreamTranscriptionResponseHandler getResponseHandler(OutputCollector outputCollector) {

        return StartStreamTranscriptionResponseHandler.builder()
                .onResponse(r -> {
                    System.out.println(
                            String.format("=== Received Initial response. Request Id: %s ===",
                                    r.requestId()));
                })
                .onError(e -> {
                    System.out.println("Error in middle of stream " + e.getMessage());
                    System.out.println("Error in middle of stream " + e.toString());
                })
                .onComplete(() -> {
                    System.out.println("Stream completed");
                    System.out.println(outputCollector.getOutput());
                })
                .subscriber(event -> {
                    List<Result> results = ((TranscriptEvent) event).transcript().results();
                    System.out.println("got results");
                    if (results.size() > 0) {
                        System.out.println("results > 0");
                        if (results.get(0).alternatives().size() > 0) {
                            if (!results.get(0).alternatives().get(0).transcript().isEmpty()) {
                                String transcript = results.get(0).alternatives().get(0).transcript();
                                outputCollector.collect(transcript);
                                System.out.println(
                                        String.format("Thread %s: %s",
                                                Thread.currentThread().getName(),
                                                transcript
                                        )
                                );
                            }
                        }
                    }
                })
                .build();
    }

    private static class AudioStreamPublisher implements Publisher<AudioStream> {
        private final InputStream inputStream;

        private AudioStreamPublisher(InputStream inputStream) {
            this.inputStream = inputStream;
        }

        @Override
        public void subscribe(Subscriber<? super AudioStream> s) {
            s.onSubscribe(new SubscriptionImpl(s, inputStream));
        }
    }

    private static AwsCredentialsProvider getCredentials() {
        return StaticCredentialsProvider.create(AwsBasicCredentials.create(System.getenv("OVERRIDE_AWS_ACCESS_KEY_ID"), System.getenv("OVERRIDE_AWS_SECRET_ACCESS_KEY")));
    }

    private static class SubscriptionImpl implements Subscription {
        private static final int CHUNK_SIZE_IN_BYTES = 1024 * 2;
        private ExecutorService executor = Executors.newFixedThreadPool(1);
        private AtomicLong demand = new AtomicLong(0);

        private final Subscriber<? super AudioStream> subscriber;
        private final InputStream inputStream;

        private SubscriptionImpl(Subscriber<? super AudioStream> s, InputStream inputStream) {
            this.subscriber = s;
            this.inputStream = inputStream;
        }

        @Override
        public void request(long n) {
            if (n <= 0) {
                subscriber.onError(new IllegalArgumentException("Demand must be positive"));
            }

            demand.getAndAdd(n);

            if (executor.isShutdown()) {
                subscriber.onComplete();
            } else {
                executor.submit(() -> {
                    try {
                        do {
                            ByteBuffer audioBuffer = getNextEvent();
                            if (audioBuffer.remaining() > 0) {
                                AudioEvent audioEvent = audioEventFromBuffer(audioBuffer);
                                subscriber.onNext(audioEvent);
                                Thread.sleep(100);
                            } else {
                                subscriber.onComplete();
                                break;
                            }
                        } while (demand.decrementAndGet() > 0);
                    } catch (Exception e) {
                        subscriber.onError(e);
                    }
                });
            }
        }

        @Override
        public void cancel() {
            executor.shutdown();
        }

        private ByteBuffer getNextEvent() {
            ByteBuffer audioBuffer = null;
            byte[] audioBytes = new byte[CHUNK_SIZE_IN_BYTES];

            int len = 0;
            try {
                len = inputStream.read(audioBytes);

                if (len <= 0) {
                    audioBuffer = ByteBuffer.allocate(0);
                } else {
                    audioBuffer = ByteBuffer.wrap(audioBytes, 0, len);
                }
            } catch (IOException e) {
                throw new UncheckedIOException(e);
            }

            return audioBuffer;
        }

        private AudioEvent audioEventFromBuffer(ByteBuffer bb) {
            return AudioEvent.builder()
                    .audioChunk(SdkBytes.fromByteBuffer(bb))
                    .build();
        }

    }
}
