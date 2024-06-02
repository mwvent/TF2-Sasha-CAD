# SashaPI Motor and LED Driver
import supervisor
import time
import board
import digitalio
import neopixel
import random
from pwmio import PWMOut
from adafruit_motor import motor as Motor
import audiocore
import audiopwmio
import asyncio

class Sasha() :
	# Pins Config
	# 5v input (from external regulator) to vsys
	#onboard_led = digitalio.DigitalInOut(board.LED)
	#onboard_led.direction = digitalio.Direction.OUTPUT
	motor_a_pin = board.GP18
	motor_b_pin = board.GP19
	speaker_a_pin = board.GP20
	speaker_b_pin = board.GP21
	pixel_pin = board.GP22
	#pixel2_pin = board.GP26
	spin_button_pin = board.GP27
	trigger_button_pin = board.GP28
	on_button_pin = board.GP15
	
	# Setup pins 
	spin_button = digitalio.DigitalInOut(spin_button_pin)
	spin_button.direction = digitalio.Direction.INPUT
	spin_button.pull = digitalio.Pull.UP
	trigger_button = digitalio.DigitalInOut(trigger_button_pin)
	trigger_button.direction = digitalio.Direction.INPUT
	trigger_button.pull = digitalio.Pull.UP
	on_button = digitalio.DigitalInOut(on_button_pin)
	on_button.direction = digitalio.Direction.INPUT
	on_button.pull = digitalio.Pull.UP
	motor = Motor.DCMotor(PWMOut(motor_a_pin, frequency=50), PWMOut(motor_b_pin, frequency=50))
	pixels = neopixel.NeoPixel(pixel_pin, 7, brightness=1, auto_write=False)

	pixels_map_indicatorlight = [0]
	pixels_map_outsidebarrel = [1, 2, 3, 4]
	pixels_map_insidebarrel = [5, 6]

	# in ms
	spinning_delay = 250
	firing_delay = 5
	idle_delay = 500
	# should be multiples of firing_delay
	firing_blink_on_delay = 50
	firing_blink_off_delay = 25

	# Speeds
	led_tick_ms = 5
	spin_up_perc = 0.25 # percentage of max speed that spin up reaches
	spin_up_inc_per_tick = 0.01 # percentage to increase spin up on tick
	spin_down_dec_per_tick = 0.01 # percentage to decrease spin down on tick
	motor_tick_ms = 200 # higher speeds = longer spinup time
	motor_max_perc = 1 # value < 1 to cap top speed
	
	# Main Loop V2
	next_motor_tick = 0
	motor_ticks_countdown = 0
	next_led_tick = 0
	led_ticks_countdown = 0
	led_firing_on = False
	last_spin_pressed = False
	last_trigger_pressed = False
	last_on_pressed = False
	toggled_on = False
	toggled_spin = False
	audioState = 0
	
	def __init__(self) :
		print("Sasha powering on")
		# Startup
		startupcols = [(255,0,0),(255,255,0),(0,255,255),(0,0,255),(255,255,255)]
		for c in startupcols :
			self.pixels.fill(c)
			self.pixels.show()
			time.sleep(0.2)
			
	def run(self) -> None :
		asyncio.run(self.arun())
		
	async def arun(self) -> None :
		"""
		Start Running Instance Async
		"""
		await asyncio.gather(
			asyncio.create_task(self.poll_states()),
			asyncio.create_task(self.poll_motor()),
			asyncio.create_task(self.poll_pixels()),
			asyncio.create_task(self.poll_audio()),
		)

	def mappedPixelsSetAll(self, fpixels, map, col) :
		for p in map :
			fpixels[p] = col

	def randFiringPixel(self) :
		r = random.random()
		if r >= 0.3 :
			R = r * 255
			G = r * 128
		else :
			R = 0
			G = 0
		return (R, G, 0)

	def mappedPixelsSetFire(self, fpixels, map) :
		for p in map :
			fpixels[p] = self.randFiringPixel()
			
	async def poll_audio(self) :
		speaker = audiopwmio.PWMAudioOut(self.speaker_a_pin)
		speaker_b_out = digitalio.DigitalInOut(self.speaker_b_pin)
		speaker_b_out.direction = digitalio.Direction.OUTPUT
		speaker_b_out.value = False
		audioState = 0
		wav_powerOn = audiocore.WaveFile("/wav/poweron.wav")
		wav_shoot = audiocore.WaveFile("/wav/shoot.wav")
		wav_spin = audiocore.WaveFile("/wav/spin.wav")
		wav_windup = audiocore.WaveFile("/wav/windup.wav")
		wav_winddown = audiocore.WaveFile("/wav/winddown.wav")
		print("Audio loaded")
		speaker.play(wav_powerOn)
		while True :
			await asyncio.sleep(0.1)
			# if audio in any state and toggled_on becomes false drop to state 0 immediatley
			if audioState != 0 and not self.toggled_on :
				audioState = 0
				if speaker.playing :
					speaker.stop() 
			# 0 = off state, wait for toggled_on
			if audioState == 0 : 
				if self.toggled_on :
					speaker.play(wav_powerOn)
					audioState == 1
			# 1 = playing startup sound or spin down
			if audioState == 1 and not speaker.playing : # startup sound playing
				audioState == 2
			# idle in toggled_on - waits for motor spin up
			if audioState == 2 : 
				if self.motorSpeed > self.spin_up_perc * 0.2 :
					speaker.play(wav_windup)
					audioState == 3
			# playing spin up sound
			if audioState == 3 :
				# if sample finished and reached speed
				if not speaker.playing and \
					   self.motorSpeed >= self.spin_up_perc :
					audioState = 10
				# if sample finished but spin has turned off
				if not speaker.playing and not self.toggled_spin :
					speaker.play(wav_winddown)
					audioState = 1
			# spinning not firing, transition to firing if full motor 
			# transition to spin down if toggled off
			# otherwise loop spin sound
			if audioState == 10 :
				if self.motorSpeed > self.spin_up_perc :
					if speaker.playing :
						speaker.stop()
					audioState = 11
				elif not self.toggled_spin :
					if speaker.playing :
						speaker.stop()
					speaker.play(wav_winddown)
					audioState = 1
				elif not speaker.playing :
					speaker.play(wav_spin)
			# firing, transition to spinning if speed drops
			# tranisition to spin down if toggled off
			if audioState == 11 :
				if self.motorSpeed == self.spin_up_perc :
					if speaker.playing :
						speaker.stop()
					audioState = 10
				elif not self.toggled_spin :
					if speaker.playing :
						speaker.stop()
					speaker.play(wav_winddown)
					audioState = 1
				elif not speaker.playing :
					speaker.play(wav_shoot)
	
	_motorSpeed = 0 # float between 0&1			
	@property
	def motorSpeed(self) :
		return self._motorSpeed
	@motorSpeed.setter
	def motorSpeed(self, value : int) :
		self._motorSpeed = value if value >= 0 else 0
		self.motor.throttle = self._motorSpeed * self.motor_max_perc
			
	async def poll_motor(self) :
		nextSleep = 0
		idleSleepTime = 2
		while True :
			await asyncio.sleep(nextSleep/1000)
			# Toggling off = immediate stop
			if not self.toggled_on:
				self.motorSpeed = 0
				nextSleep = idleSleepTime
				continue
			# Spin turned off and motor off
			if not self.toggled_spin and self.motorSpeed == 0 :
				nextSleep = 10
				continue
			# Spin turned off
			# slowly decrement speed if speed > 0
			if not self.toggled_spin :
				self.motorSpeed -= self.spin_down_dec_per_tick
				nextSleep = self.motor_tick_ms
				continue
			spinUpReady = self.motorSpeed >= self.spin_up_perc
			# Go full speed on trigger press but only if spin up is ready
			if self.toggled_spin and self.trigger_pressed and spinUpReady:
				self.motorSpeed = 1
				nextSleep = 1
				continue
			# Still spinning up
			if self.toggled_spin and not spinUpReady :
				self.motorSpeed = min(
					self.motorSpeed + spin_up_inc_per_tick,
					self.spin_up_perc
				)
			# Maintaining spin up
			# State here should be toggled spin, spinupready and not firing
			self.motorSpeed = self.spin_up_perc
			nextSleep = 1
	
	async def poll_pixels(self) :
		pixels = self.pixels
		pixels_map_indicatorlight = self.pixels_map_indicatorlight
		pixels_map_insidebarrel = self.pixels_map_insidebarrel
		pixels_map_outsidebarrel = self.pixels_map_outsidebarrel
		tickCounter = 0
		while True :
			await asyncio.sleep(self.led_tick_ms/1000)
			if not self.toggled_on:
				pixels.fill((0,0,0))
				pixels.show()
				continue
			# Led Animation
			if self.motorSpeed == 0 : # on but idle
				pixels.fill((0,0,0))
				self.mappedPixelsSetAll(
					pixels, pixels_map_indicatorlight, (0,0,255)
				)
				tickCounter = 0
			elif self.motorSpeed < self.spin_up_perc : # spinning up
				tickCounter -= 1
				tickCounter = 100 if tickCounter <=0 else tickCounter
				# 50% of time off
				pixels.fill((0,0,0))
				# other 50% a transition from blue to green
				# depending on spin up
				if tickCounter < 50 :
					percSpunUp = (self.motorSpeed / self.spin_up_perc)
					G = int(percSpunUp * 0xFF)
					B = 0xFF - int(percSpunUp * 0xFF)
					self.mappedPixelsSetAll(
						pixels,pixels_map_indicatorlight, (0,G,B)
					)
			elif self.motorSpeed == self.spin_up_perc : # spun up set ind green
				pixels.fill((0,0,0))
				self.mappedPixelsSetAll(
					pixels, pixels_map_indicatorlight, (0,255,0)
				)
			elif self.motorSpeed > self.spin_up_perc : # firing
				tickCounter -= 1
				if tickCounter <= 0 :
					tickCounter = 10
					self.mappedPixelsSetFire(
						pixels, pixels_map_insidebarrel
					)
					self.mappedPixelsSetFire(
						pixels, pixels_map_outsidebarrel
					)
					self.mappedPixelsSetAll(
						pixels, pixels_map_indicatorlight, (255,255,0)
					)
			else : # off
				pixels.fill((0, 0, 0))
			pixels.show()
	
	async def poll_states(self) :
		last_spin_pressed = False
		last_trigger_pressed = False
		last_on_pressed = False
		while True :
			await asyncio.sleep(0)
			currentTick = supervisor.ticks_ms()
			# Get input states
			spin_pressed = not self.spin_button.value # NO
			trigger_pressed = self.trigger_button.value # NC
			on_pressed = not self.on_button.value # NO

			# Have Input States Changed?
			stateChanged = \
				last_spin_pressed != spin_pressed \
				or last_trigger_pressed != trigger_pressed or \
				last_on_pressed != on_pressed
			if stateChanged :
				spin_button_released = not spin_pressed and last_spin_pressed
				if spin_button_released :
					self.toggled_spin = not self.toggled_spin
				on_button_released = not on_pressed and last_on_pressed
				if on_button_released :
					self.toggled_on = not self.toggled_on
					self.toggled_spin = False
				last_spin_pressed = spin_pressed
				last_trigger_pressed = trigger_pressed
				last_on_pressed = on_pressed		

sasha = Sasha()
sasha.run()

