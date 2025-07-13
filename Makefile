
binlocal: 
	go build -ldflags "$(LDFLAGS)" -o /tmp/apptemplate ./main.go

buf:
	buf generate
