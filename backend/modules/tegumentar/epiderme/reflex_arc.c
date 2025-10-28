#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>

#define DDOS_THRESHOLD 1000
#define TIME_WINDOW_NS 100000000ULL /* 100 ms */

struct syn_key {
    __u32 src_ip;
};

struct syn_value {
    __u64 last_ts;
    __u32 count;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 65536);
    __type(key, struct syn_key);
    __type(value, struct syn_value);
} syn_rate_map SEC(".maps");

struct event {
    __u32 src_ip;
    __u32 signature_id;
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
} reflex_events SEC(".maps");

static __always_inline int detect_sql_signature(void *data, void *data_end, struct tcphdr *tcph) {
    void *payload = (void *)tcph + tcph->doff * 4;
    if (payload >= data_end)
        return 0;

    char signature[5];
    if (payload + 5 > data_end)
        return 0;

    if (bpf_probe_read(signature, sizeof(signature), payload) < 0)
        return 0;

    if ((signature[0] == 'U' || signature[0] == 'u') &&
        (signature[1] == 'N' || signature[1] == 'n') &&
        (signature[2] == 'I' || signature[2] == 'i') &&
        (signature[3] == 'O' || signature[3] == 'o') &&
        (signature[4] == 'N' || signature[4] == 'n')) {
        return 1;
    }
    return 0;
}

static __always_inline int handle_tcp(struct xdp_md *ctx, void *data, void *data_end, struct iphdr *iph) {
    struct tcphdr *tcph = data + sizeof(struct ethhdr) + sizeof(struct iphdr);
    if ((void *)(tcph + 1) > data_end)
        return XDP_PASS;

    if (tcph->syn && !tcph->ack) {
        struct syn_key key = {.src_ip = iph->saddr};
        struct syn_value *value = bpf_map_lookup_elem(&syn_rate_map, &key);
        __u64 ts = bpf_ktime_get_ns();
        if (value) {
            if (ts - value->last_ts > TIME_WINDOW_NS) {
                value->count = 1;
                value->last_ts = ts;
            } else {
                value->count += 1;
                value->last_ts = ts;
            }
        } else {
            struct syn_value new_value = {
                .last_ts = ts,
                .count = 1,
            };
            bpf_map_update_elem(&syn_rate_map, &key, &new_value, BPF_ANY);
        }

        value = bpf_map_lookup_elem(&syn_rate_map, &key);
        if (value && value->count > DDOS_THRESHOLD) {
            struct event evt = {
                .src_ip = iph->saddr,
                .signature_id = 1,
            };
            bpf_perf_event_output(ctx, &reflex_events, BPF_F_CURRENT_CPU, &evt, sizeof(evt));
            return XDP_DROP;
        }
    }

    if (detect_sql_signature(data, data_end, tcph)) {
        struct event evt = {
            .src_ip = iph->saddr,
            .signature_id = 2,
        };
        bpf_perf_event_output(ctx, &reflex_events, BPF_F_CURRENT_CPU, &evt, sizeof(evt));
        return XDP_DROP;
    }
    return XDP_PASS;
}

SEC("xdp")
int xdp_reflex_firewall(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *iph = data + sizeof(struct ethhdr);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    if (iph->protocol == IPPROTO_TCP) {
        return handle_tcp(ctx, data, data_end, iph);
    }

    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
