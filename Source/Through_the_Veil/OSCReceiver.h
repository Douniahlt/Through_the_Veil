// OSCReceiver.h

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "OSCServer.h"
#include "OSCMessage.h"
#include "OSCReceiver.generated.h"

UCLASS()
class THROUGHTHEVEIL_API AOSCReceiver : public AActor
{
	GENERATED_BODY()

public:
	// Constructor
	AOSCReceiver();

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	// Called when the game ends
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:
	// Called every frame
	virtual void Tick(float DeltaTime) override;

private:
	// Le serveur OSC
	UPROPERTY()
	UOSCServer* OSCServer;

	// Callback appelé quand un message OSC arrive
	void OnOSCMessageReceived(const FOSCMessage& Message, const FString& IPAddress, int32 Port);

	// Port d'écoute (modifiable dans l'éditeur)
	UPROPERTY(EditAnywhere, Category = "OSC Settings")
	int32 ListenPort = 8000;

	// Adresse IP d'écoute (modifiable dans l'éditeur)
	UPROPERTY(EditAnywhere, Category = "OSC Settings")
	FString ListenAddress = TEXT("0.0.0.0");

	// Variables pour stocker les données reçues de Python
	UPROPERTY(BlueprintReadOnly, Category = "Hand Tracking", meta = (AllowPrivateAccess = "true"))
	bool bHandDetected = false;

	UPROPERTY(BlueprintReadOnly, Category = "Hand Tracking", meta = (AllowPrivateAccess = "true"))
	FVector2D HandPosition = FVector2D(0.5f, 0.5f);

	UPROPERTY(BlueprintReadOnly, Category = "Hand Tracking", meta = (AllowPrivateAccess = "true"))
	float HandIntensity = 0.0f;

public:
	// Getters pour Blueprint
	UFUNCTION(BlueprintCallable, Category = "Hand Tracking")
	bool IsHandDetected() const { return bHandDetected; }

	UFUNCTION(BlueprintCallable, Category = "Hand Tracking")
	FVector2D GetHandPosition() const { return HandPosition; }

	UFUNCTION(BlueprintCallable, Category = "Hand Tracking")
	float GetHandIntensity() const { return HandIntensity; }
};