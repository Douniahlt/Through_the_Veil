// OSCReceiver.cpp

#include "OSCReceiver.h"
#include "OSCManager.h"

// Constructor
AOSCReceiver::AOSCReceiver()
{
	// Active le Tick pour cet Actor
	PrimaryActorTick.bCanEverTick = true;
}

// Called when the game starts
void AOSCReceiver::BeginPlay()
{
	Super::BeginPlay();

	UE_LOG(LogTemp, Warning, TEXT("================================================="));
	UE_LOG(LogTemp, Warning, TEXT("🎭 THROUGH THE VEIL - OSC Receiver"));
	UE_LOG(LogTemp, Warning, TEXT("================================================="));

	// Crée le serveur OSC
	OSCServer = UOSCManager::CreateOSCServer(
		ListenAddress,      // Adresse (0.0.0.0 = écoute tout)
		ListenPort,         // Port (8000)
		false,              // Multicast loopback
		this                // Outer object
	);

	if (OSCServer)
	{
		UE_LOG(LogTemp, Warning, TEXT("✅ Serveur OSC créé"));
		UE_LOG(LogTemp, Warning, TEXT("   Adresse : %s"), *ListenAddress);
		UE_LOG(LogTemp, Warning, TEXT("   Port : %d"), ListenPort);
		UE_LOG(LogTemp, Warning, TEXT("================================================="));

		// Bind le callback pour TOUS les messages OSC reçus
		OSCServer->OnOscMessageReceived.AddUObject(this, &AOSCReceiver::OnOSCMessageReceived);

		UE_LOG(LogTemp, Warning, TEXT("🎧 En attente de messages OSC..."));
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("================================================="));
		UE_LOG(LogTemp, Error, TEXT("❌ ERREUR : Impossible de créer le serveur OSC"));
		UE_LOG(LogTemp, Error, TEXT("   Vérifiez que le plugin OSC est activé"));
		UE_LOG(LogTemp, Error, TEXT("   Vérifiez que le port %d n'est pas déjà utilisé"), ListenPort);
		UE_LOG(LogTemp, Error, TEXT("================================================="));
	}
}

// Called when the game ends
void AOSCReceiver::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// Arrête et nettoie le serveur OSC
	if (OSCServer)
	{
		UE_LOG(LogTemp, Warning, TEXT("🛑 Arrêt du serveur OSC..."));
		OSCServer->Stop();
		OSCServer = nullptr;
	}

	Super::EndPlay(EndPlayReason);
}

// Called every frame
void AOSCReceiver::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// On pourrait utiliser Tick pour faire des choses avec les données
	// Mais pour l'instant, tout se passe dans le callback
}

// Callback appelé à chaque message OSC reçu
void AOSCReceiver::OnOSCMessageReceived(const FOSCMessage& Message, const FString& IPAddress, int32 Port)
{
	// Récupère l'adresse OSC (ex: /hand/detected)
	FString Address = Message.GetAddress();

	// Log le message reçu
	UE_LOG(LogTemp, Display, TEXT("📥 OSC : %s (de %s:%d)"), *Address, *IPAddress, Port);

	// Parse selon l'adresse du message
	if (Address == TEXT("/hand/detected"))
	{
		// /hand/detected contient 1 argument : int (0 ou 1)
		const TArray<FOSCArgument>& Args = Message.GetArguments();

		if (Args.Num() > 0)
		{
			int32 Detected = 0;
			if (Args[0].AsInt32(Detected))
			{
				bHandDetected = (Detected == 1);
				UE_LOG(LogTemp, Display, TEXT("   └─> Main : %s"), bHandDetected ? TEXT("✓ DÉTECTÉE") : TEXT("✗ Absente"));
			}
		}
	}
	else if (Address == TEXT("/hand/position"))
	{
		// /hand/position contient 2 arguments : float x, float y
		const TArray<FOSCArgument>& Args = Message.GetArguments();

		if (Args.Num() >= 2)
		{
			float X = 0.0f;
			float Y = 0.0f;

			if (Args[0].AsFloat(X) && Args[1].AsFloat(Y))
			{
				HandPosition = FVector2D(X, Y);
				UE_LOG(LogTemp, Display, TEXT("   └─> Position : x=%.3f, y=%.3f"), X, Y);
			}
		}
	}
	else if (Address == TEXT("/hand/intensity"))
	{
		// /hand/intensity contient 1 argument : float
		const TArray<FOSCArgument>& Args = Message.GetArguments();

		if (Args.Num() > 0)
		{
			float Intensity = 0.0f;
			if (Args[0].AsFloat(Intensity))
			{
				HandIntensity = Intensity;
				UE_LOG(LogTemp, Display, TEXT("   └─> Intensité : %.3f"), Intensity);
			}
		}
	}
	else
	{
		// Message OSC non reconnu
		UE_LOG(LogTemp, Warning, TEXT("   └─> Adresse inconnue : %s"), *Address);
	}
}