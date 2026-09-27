// AI Thinker ESP32-CAM / OV2640. This board never drives the motors.
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <esp_camera.h>
#include <esp_timer.h>

namespace {
constexpr uint32_t WIFI_TIMEOUT = 20000;
WebServer http(80);
DNSServer dns;
Preferences preferences;
struct Credentials {
	uint32_t magic;
	char ssid[33];
	char password[65];
};
Credentials saved{}, candidate{};
bool storageReady = false, cameraReady = false, portalOpen = false;
bool testing = false, joining = false, online = false, restarting = false;
uint32_t joinStarted = 0, restartAt = 0, sequence = 0, lastAdvertise = 0;
bool mdnsReady = false;
String hostname, message = "Informe a mesma rede Wi-Fi de 2,4 GHz usada pelo computador e pelo ESP8266.";

bool valid(const Credentials& value) {
	return value.magic == 0x43414D31 && value.ssid[0] &&
		memchr(value.ssid, 0, sizeof(value.ssid)) && memchr(value.password, 0, sizeof(value.password));
}

void join(const Credentials& value) {
	WiFi.disconnect();
	WiFi.begin(value.ssid, value.password);
	joinStarted = millis();
	joining = true;
}

bool startCamera() {
	if (!psramFound()) {
		Serial.println("[CAMERA] PSRAM não encontrada");
		return false;
	}
	camera_config_t config = {};
	config.ledc_channel = LEDC_CHANNEL_0;
	config.ledc_timer = LEDC_TIMER_0;
	config.pin_d0 = 5;
	config.pin_d1 = 18;
	config.pin_d2 = 19;
	config.pin_d3 = 21;
	config.pin_d4 = 36;
	config.pin_d5 = 39;
	config.pin_d6 = 34;
	config.pin_d7 = 35;
	config.pin_xclk = 0;
	config.pin_pclk = 22;
	config.pin_vsync = 25;
	config.pin_href = 23;
	config.pin_sccb_sda = 26;
	config.pin_sccb_scl = 27;
	config.pin_pwdn = 32;
	config.pin_reset = -1;
	config.xclk_freq_hz = 20000000;
	config.pixel_format = PIXFORMAT_JPEG;
	config.frame_size = FRAMESIZE_QVGA;
	config.jpeg_quality = 12;
	config.fb_count = 1;
	config.fb_location = CAMERA_FB_IN_PSRAM;
	config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
	esp_err_t result = esp_camera_init(&config);
	if (result != ESP_OK) {
		Serial.printf("[CAMERA] Falha de inicialização: 0x%x\n", result);
		return false;
	}
	sensor_t* sensor = esp_camera_sensor_get();
	sensor->set_hmirror(sensor, 0);
	sensor->set_vflip(sensor, 0);
	return true;
}

void capture() {
	if (!online || portalOpen || !cameraReady) {
		http.send(503, "text/plain", "Camera indisponivel");
		return;
	}
	// Drop the queued exposure; acquire a new frame for this request.
	camera_fb_t* frame = esp_camera_fb_get();
	if (frame) esp_camera_fb_return(frame);
	frame = esp_camera_fb_get();
	if (!frame) {
		http.send(503, "text/plain", "Falha na captura");
		return;
	}
	int64_t captured = int64_t(frame->timestamp.tv_sec) * 1000000 + frame->timestamp.tv_usec;
	int64_t age = (esp_timer_get_time() - captured) / 1000;
	if (age < 0 || age > 150 || frame->format != PIXFORMAT_JPEG || frame->len > 160000) {
		esp_camera_fb_return(frame);
		http.send(503, "text/plain", "Imagem antiga ou invalida");
		return;
	}
	http.sendHeader("Cache-Control", "no-store");
	http.sendHeader("X-Fusca-Frame", String(++sequence));
	http.sendHeader("X-Fusca-Age-Ms", String(static_cast<uint32_t>(age)));
	http.setContentLength(frame->len);
	http.send(200, "image/jpeg", "");
	WiFiClient client = http.client();
	client.setTimeout(1); // ESP32 Arduino WiFiClient uses seconds here.
	size_t length = frame->len;
	size_t sent = client.write(frame->buf, length);
	esp_camera_fb_return(frame);
	if (sent != length) client.stop();
}

void page() {
	if (!portalOpen) {
		http.send(200, "text/html; charset=utf-8", cameraReady
			? "<meta charset='utf-8'><h1>Fusca Azul — ESP32-CAM</h1><p>Câmera pronta. Conecte pelo aplicativo Fusca Azul.</p><a href='/capture'>Ver imagem</a>"
			: "<meta charset='utf-8'><h1>Câmera indisponível</h1><p>Verifique o cabo da OV2640, a alimentação e o monitor serial.</p>");
		return;
	}
	String html = "<!doctype html><html lang='pt-BR'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Fusca CAM</title><style>body{font:18px sans-serif;max-width:440px;margin:40px auto;padding:20px;background:#182031;color:#e7edf7}input,button{box-sizing:border-box;width:100%;padding:12px;margin:8px 0}button{background:#bcd6f6}</style><h1>Conectar a ESP32-CAM</h1><p>";
	html += message;
	html += "</p><form method='post' action='/wifi'><label>Nome da rede<input name='ssid' maxlength='32' required></label><label>Senha<input type='password' name='password' maxlength='64'></label><button>Conectar e salvar</button></form><p>Deixe a senha vazia apenas em redes abertas.</p><a style='color:#bcd6f6' href='/'>Atualizar situação</a></html>";
	http.sendHeader("Cache-Control", "no-store");
	http.send(200, "text/html; charset=utf-8", html);
}

void openPortal() {
	WiFi.mode(WIFI_AP_STA);
	WiFi.softAP(hostname.c_str());
	dns.start(53, "*", WiFi.softAPIP());
	portalOpen = true;
	Serial.printf("[WIFI] Configure na rede %s em http://192.168.4.1\n", hostname.c_str());
}

void configure() {
	if (!portalOpen || testing || restarting || !storageReady) {
		http.send(409, "text/plain; charset=utf-8", "Configuração indisponível ou em andamento.");
		return;
	}
	String ssid = http.arg("ssid"), password = http.arg("password");
	bool passwordValid = password.isEmpty() || (password.length() >= 8 && password.length() <= 63);
	if (password.length() == 64) {
		passwordValid = true;
		for (unsigned i = 0; i < 64; ++i) if (!isxdigit(password[i])) passwordValid = false;
	}
	if (ssid.isEmpty() || ssid.length() > 32 || !passwordValid || strlen(ssid.c_str()) != ssid.length() || strlen(password.c_str()) != password.length()) {
		http.send(400, "text/plain; charset=utf-8", "Nome ou senha inválidos.");
		return;
	}
	candidate = {};
	candidate.magic = 0x43414D31;
	ssid.toCharArray(candidate.ssid, sizeof(candidate.ssid));
	password.toCharArray(candidate.password, sizeof(candidate.password));
	message = "Testando a conexão por até 20 segundos. Atualize esta página. Após salvar, a câmera reinicia.";
	page();
	testing = true;
	join(candidate);
}

void networkLoop() {
	if (portalOpen) dns.processNextRequest();
	http.handleClient();
	if (restarting) {
		if (millis() - restartAt >= 1500) ESP.restart();
		return;
	}
	if (joining && WiFi.status() == WL_CONNECTED) {
		joining = false;
		if (testing) {
			testing = false;
			if (preferences.putBytes("wifi", &candidate, sizeof(candidate)) != sizeof(candidate)) {
				message = "Falha ao salvar a configuração. Tente novamente.";
				WiFi.disconnect();
				return;
			}
			message = "Rede salva. Reiniciando…";
			restarting = true;
			restartAt = millis();
			return;
		}
		online = true;
		if (portalOpen) {
			dns.stop();
			WiFi.softAPdisconnect(true);
			WiFi.mode(WIFI_STA);
			portalOpen = false;
		}
		lastAdvertise = millis() - 5000;
		Serial.printf("[WIFI] Câmera em http://%s/capture\n", WiFi.localIP().toString().c_str());
	}
	if (joining && millis() - joinStarted >= WIFI_TIMEOUT) {
		joining = testing = false;
		WiFi.disconnect();
		message = "Não foi possível conectar. Confira a rede e a senha. A configuração anterior foi mantida.";
		if (!portalOpen) openPortal();
	}
	if (online && WiFi.status() != WL_CONNECTED) {
		online = mdnsReady = false;
		MDNS.end();
		join(saved);
	}
	if (online && !mdnsReady && millis() - lastAdvertise >= 5000) {
		lastAdvertise = millis();
		mdnsReady = MDNS.begin(hostname.c_str());
		if (mdnsReady) {
			MDNS.addService("fusca-cam", "tcp", 80);
			MDNS.addServiceTxt("fusca-cam", "tcp", "version", "1");
			MDNS.addServiceTxt("fusca-cam", "tcp", "path", "/capture");
		}
	}
	if (portalOpen && !joining && valid(saved) && millis() - joinStarted >= 30000) join(saved);
}
}

void setup() {
	Serial.begin(115200);
	hostname = "fusca-cam-" + String(static_cast<uint32_t>(ESP.getEfuseMac()), HEX);
	WiFi.persistent(false);
	WiFi.mode(WIFI_STA);
	WiFi.setAutoReconnect(false);
	WiFi.setHostname(hostname.c_str());
	WiFi.setSleep(false);
	storageReady = preferences.begin("fusca-cam", false);
	if (storageReady && preferences.getBytesLength("wifi") == sizeof(saved)) preferences.getBytes("wifi", &saved, sizeof(saved));
	cameraReady = startCamera();
	http.on("/", HTTP_GET, page);
	http.on("/capture", HTTP_GET, capture);
	http.on("/wifi", HTTP_POST, configure);
	http.onNotFound([]() {
		if (portalOpen) {
			http.sendHeader("Location", "http://192.168.4.1/");
			http.send(302, "text/plain", "");
		} else http.send(404, "text/plain", "Not found");
	});
	http.begin();
	if (valid(saved)) join(saved);
	else openPortal();
}

void loop() {
	networkLoop();
	delay(1);
}
