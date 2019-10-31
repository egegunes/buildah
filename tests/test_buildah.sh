#!/bin/bash -e

# Log program and kernel versions
echo "Important package versions:"
(
    uname -r
    rpm -qa | egrep 'buildah|podman|conmon|crun|runc|iptable|slirp|systemd' | sort
) | sed -e 's/^/  /'

# Log environment; or at least the useful bits
echo "Environment:"
env | grep -v LS_COLORS= | sort | sed -e 's/^/  /'

export BUILDAH_BINARY=/usr/bin/buildah
export IMGTYPE_BINARY=/usr/bin/buildah-imgtype

###############################################################################
# BEGIN setup/teardown

# Start a registry
pre_bats_setup() {
    AUTHDIR=/tmp/buildah-tests-auth.$$
    mkdir -p $AUTHDIR

    CERT=$AUTHDIR/domain.crt
    if [ ! -e $CERT ]; then
        openssl req -newkey rsa:4096 -nodes -sha256 \
                -keyout $AUTHDIR/domain.key -x509 -days 2 \
                -out $AUTHDIR/domain.crt \
                -subj "/C=US/ST=Foo/L=Bar/O=Red Hat, Inc./CN=localhost"
    fi

    if [ ! -e $AUTHDIR/htpasswd ]; then
        podman run --rm --entrypoint htpasswd registry:2 \
               -Bbn testuser testpassword > $AUTHDIR/htpasswd
    fi

    podman rm -f registry || true
    podman run -d -p 5000:5000 \
           --name registry \
           -v $AUTHDIR:/auth:Z \
           -e "REGISTRY_AUTH=htpasswd" \
           -e "REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm" \
           -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
           -e REGISTRY_HTTP_TLS_CERTIFICATE=/auth/domain.crt \
           -e REGISTRY_HTTP_TLS_KEY=/auth/domain.key \
           registry:2
}

post_bats_teardown() {
    podman rm -f registry
}

# END   setup/teardown
###############################################################################
# BEGIN actual test

pre_bats_setup
bats /usr/share/buildah/test/system
rc=$?
post_bats_teardown

exit $rc
