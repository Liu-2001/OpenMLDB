package com._4paradigm.rtidb.client;

import java.nio.ByteBuffer;

import org.junit.Assert;
import org.junit.Test;

import com._4paradigm.rtidb.client.impl.KvIterator;
import com._4paradigm.rtidb.client.impl.TabletClient;

public class TabletClientTest {

    private String host = "127.0.0.1";
    private int port = 9501;

    @Test
    public void test0Create() {
        TabletClient client = new TabletClient(host, port);
        try {
            client.init();
        } catch (InterruptedException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            Assert.assertFalse(true);
        }
        boolean ok = client.createTable("tj0", 20, 1, 0);
        Assert.assertTrue(ok);
        ok = client.createTable("tj0", 20, 1, 0);
        Assert.assertFalse(ok);
        client.close();
    }

    @Test
    public void test1Put() {
        TabletClient client = new TabletClient(host, port);
        try {
            client.init();
        } catch (InterruptedException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            Assert.assertFalse(true);
        }
        Assert.assertFalse(client.put(22, 1, "pk", 9527, "test0"));
        boolean ok = client.createTable("tj1", 21, 1, 0);
        Assert.assertTrue(ok);
        ok = client.put(21, 1,"pk", 9527, "test0");
        Assert.assertTrue(ok);
        client.close();
    }

    @Test
    public void test3Scan() {
        TabletClient client = new TabletClient(host, port);
        try {
            client.init();
        } catch (InterruptedException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            Assert.assertFalse(true);
        }
        KvIterator it = client.scan(24, 1, "pk", 9527, 9526);
        Assert.assertNull(it);
        boolean ok = client.createTable("tj1", 23, 1, 0);
        Assert.assertTrue(ok);
        ok = client.put(23, 1,"pk", 9527, "test0");
        Assert.assertTrue(ok);
        it = client.scan(23, 1, "pk", 9527l, 9526l);
        Assert.assertTrue(it != null);
        Assert.assertTrue(it.valid());
        Assert.assertEquals(9527l, it.getKey());
        ByteBuffer bb = it.getValue();
        Assert.assertEquals(5, bb.limit() - bb.position());
        byte[] buf = new byte[5];
        bb.get(buf);
        Assert.assertEquals("test0", new String(buf));
        it.next();
        client.close();
    }

    @Test
    public void test4Drop() {
        TabletClient client = new TabletClient(host, port);
        try {
            client.init();
        } catch (InterruptedException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            Assert.assertFalse(true);
        }
        boolean ok = client.dropTable(9527, 1);
        Assert.assertFalse(ok);
        ok = client.createTable("tj1", 9527, 1, 0);
        Assert.assertTrue(ok);
        ok = client.dropTable(9527, 1);
        Assert.assertTrue(ok);
        client.close();
    }
}