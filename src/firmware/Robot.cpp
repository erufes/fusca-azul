#include "Robot.h"

Robot::Robot(Motor& leftMotor, Motor& rightMotor, Gy80& gyro)
	: gyro_(gyro), leftMotor_(leftMotor), rightMotor_(rightMotor) {}

void Robot::begin() {
	leftMotor_.begin();
	rightMotor_.begin();
	state_.set("PARADO");
}

void Robot::command(Motion next) {
	lastCommand_ = millis();
	if (!gyro_.ready()) {
		stop();
		stabilization_.set("BLOQUEADO", "Giroscopio sem calibracao ou leitura valida");
		return;
	}
	if (motion_ == next) return; // Repeated TCP commands must not reset the heading.
	heading_.reset();
	motion_ = next;
	const char* label = next == Motion::Forward ? "FRENTE" : next == Motion::Backward ? "RE" :
		next == Motion::Left ? "ESQUERDA" : "DIREITA";
	state_.set(label);
	stabilization_.set(next == Motion::Forward || next == Motion::Backward ? "ATIVO" : "CURVA_MANUAL");
	drive(HeadingControl::BASE_PWM, HeadingControl::BASE_PWM);
}

void Robot::forward() { command(Motion::Forward); }
void Robot::backward() { command(Motion::Backward); }
void Robot::left() { command(Motion::Left); }
void Robot::right() { command(Motion::Right); }

void Robot::stop() {
	motion_ = Motion::Stop;
	heading_.reset();
	leftMotor_.stop();
	rightMotor_.stop();
	state_.set("PARADO");
}

void Robot::drive(int left, int right) {
	if (motion_ == Motion::Forward || motion_ == Motion::Right) leftMotor_.forward(left);
	else leftMotor_.backward(left);
	if (motion_ == Motion::Forward || motion_ == Motion::Left) rightMotor_.forward(right);
	else rightMotor_.backward(right);
}

void Robot::update() {
	bool sample = gyro_.update(motion_ != Motion::Stop);
	if (!gyro_.ready()) {
		stop();
		stabilization_.set("BLOQUEADO", "Giroscopio sem calibracao ou leitura valida");
		return;
	}
	if (motion_ == Motion::Stop) { stabilization_.set("PARADO"); return; }
	if (millis() - lastCommand_ >= 400) {
		stop();
		stabilization_.set("SEM_COMANDO", "Sem comando recente por 400 ms");
		return;
	}
	if (!sample || (motion_ != Motion::Forward && motion_ != Motion::Backward)) return;
	int trim = heading_.update(gyro_.yawRate(), gyro_.sampleSeconds());
	int left, right;
	HeadingControl::mix(motion_ == Motion::Forward ? 1 : -1, trim, left, right);
	drive(left, right);
}
